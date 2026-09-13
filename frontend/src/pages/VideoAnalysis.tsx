import {
    useEffect,
    useState,
} from "react";

import { api } from "../services/api";

import {
    AnalysisReport,
    EventItem,
    Video,
} from "../types";


const POLL_INTERVAL = 3000;


export default function VideoAnalysis() {

    const [file, setFile] =
        useState<File | null>(null);

    const [video, setVideo] =
        useState<Video | null>(null);

    const [report, setReport] =
        useState<AnalysisReport | null>(
            null
        );

    const [events, setEvents] =
        useState<EventItem[]>([]);

    const [loading, setLoading] =
        useState(false);

    const [deleting, setDeleting] =
        useState(false);

    const [message, setMessage] =
        useState("");

    const [error, setError] =
        useState("");


    // ========================================================
    // RESTORE LAST VIDEO
    // ========================================================

    useEffect(() => {

        const savedId =
            localStorage.getItem(
                "sentinelai_last_video_id"
            );

        if (!savedId) {
            return;
        }

        const videoId =
            Number(savedId);

        if (
            !Number.isInteger(
                videoId
            )
        ) {
            return;
        }

        void restoreVideo(
            videoId
        );

    }, []);


    async function restoreVideo(
        videoId: number
    ) {

        try {

            const currentVideo =
                await api.getVideo(
                    videoId
                );

            setVideo(
                currentVideo
            );

            if (
                currentVideo.status ===
                "completed"
            ) {

                const [
                    reportData,
                    eventData,
                ] =
                    await Promise.all([
                        api.getVideoReport(
                            videoId
                        ),

                        api.getVideoEvents(
                            videoId
                        ),
                    ]);

                setReport(
                    reportData
                );

                setEvents(
                    eventData
                );
            }

        } catch (err) {

            console.error(
                err
            );

            /*
             * The saved video may have been deleted.
             * Clear the stale localStorage reference.
             */
            localStorage.removeItem(
                "sentinelai_last_video_id"
            );

            setVideo(
                null
            );

            setReport(
                null
            );

            setEvents(
                []
            );
        }
    }


    // ========================================================
    // POLL PROCESSING
    // ========================================================

    useEffect(() => {

        if (
            !video ||
            video.status !==
            "processing"
        ) {
            return;
        }

        const timer =
            window.setInterval(
                async () => {

                    try {

                        const current =
                            await api.getVideo(
                                video.id
                            );

                        setVideo(
                            current
                        );

                        if (
                            current.status ===
                            "completed"
                        ) {

                            window.clearInterval(
                                timer
                            );

                            const [
                                reportData,
                                eventData,
                            ] =
                                await Promise.all([
                                    api.getVideoReport(
                                        current.id
                                    ),

                                    api.getVideoEvents(
                                        current.id
                                    ),
                                ]);

                            setReport(
                                reportData
                            );

                            setEvents(
                                eventData
                            );

                            setLoading(
                                false
                            );

                            setMessage(
                                "Analysis completed successfully."
                            );
                        }


                        if (
                            current.status ===
                            "failed"
                        ) {

                            window.clearInterval(
                                timer
                            );

                            setLoading(
                                false
                            );

                            setError(
                                "Analysis failed. Check the backend terminal."
                            );
                        }

                    } catch (err) {

                        console.error(
                            err
                        );
                    }

                },
                POLL_INTERVAL
            );


        return () => {

            window.clearInterval(
                timer
            );

        };

    }, [
        video?.id,
        video?.status,
    ]);


    // ========================================================
    // FILE CHANGE
    // ========================================================

    function handleFileChange(
        event:
            React.ChangeEvent<HTMLInputElement>
    ) {

        const selected =
            event.target.files?.[0]
            ?? null;

        setFile(
            selected
        );

        setVideo(
            null
        );

        setReport(
            null
        );

        setEvents(
            []
        );

        setLoading(
            false
        );

        setDeleting(
            false
        );

        setMessage(
            ""
        );

        setError(
            ""
        );
    }


    // ========================================================
    // ANALYZE
    // ========================================================

    async function handleAnalyze() {

        if (!file) {

            setError(
                "Please select a video."
            );

            return;
        }

        try {

            setError(
                ""
            );

            setMessage(
                "Uploading video..."
            );

            setLoading(
                true
            );

            setReport(
                null
            );

            setEvents(
                []
            );


            const uploaded =
                await api.uploadVideo(
                    file
                );


            localStorage.setItem(
                "sentinelai_last_video_id",
                String(
                    uploaded.id
                )
            );


            setVideo(
                uploaded
            );


            await api.analyzeVideo(
                uploaded.id
            );


            setVideo({
                ...uploaded,
                status:
                    "processing",
            });


            setMessage(
                "Video uploaded. Analysis is processing..."
            );

        } catch (err) {

            setLoading(
                false
            );

            setError(
                err instanceof Error
                    ? err.message
                    : "Analysis failed."
            );
        }
    }


    // ========================================================
    // DELETE VIDEO
    // ========================================================

    async function handleDeleteVideo() {

        if (!video) {
            return;
        }

        const confirmed =
            window.confirm(
                `Delete "${video.filename}"?\n\n` +
                "This will remove the uploaded video " +
                "and its analysis record. Your trained " +
                "models and raw dataset will not be deleted."
            );

        if (!confirmed) {
            return;
        }

        try {

            setError(
                ""
            );

            setMessage(
                "Deleting video..."
            );

            setDeleting(
                true
            );

            setLoading(
                false
            );


            await api.deleteVideo(
                video.id
            );


            /*
             * Remove the saved "last video" reference
             * only if it points to this video.
             */
            const savedId =
                localStorage.getItem(
                    "sentinelai_last_video_id"
                );

            if (
                savedId ===
                String(video.id)
            ) {

                localStorage.removeItem(
                    "sentinelai_last_video_id"
                );
            }


            /*
             * Reset the current screen.
             */
            setFile(
                null
            );

            setVideo(
                null
            );

            setReport(
                null
            );

            setEvents(
                []
            );

            setMessage(
                "Video deleted successfully."
            );

        } catch (err) {

            console.error(
                err
            );

            setError(
                err instanceof Error
                    ? err.message
                    : "Failed to delete video."
            );

        } finally {

            setDeleting(
                false
            );
        }
    }


    // ========================================================
    // PERSON COUNT
    // ========================================================

    const objectCounts =
        report?.objects
            ?.unique_objects_by_class
        ?? {};


    const personCount =
        (
            objectCounts[
            "pedestrian"
            ] ?? 0
        )
        +
        (
            objectCounts[
            "people"
            ] ?? 0
        )
        +
        (
            objectCounts[
            "person"
            ] ?? 0
        );


    // ========================================================
    // VEHICLE COUNT
    // ========================================================

    const vehicleCount =
        (
            objectCounts[
            "bicycle"
            ] ?? 0
        )
        +
        (
            objectCounts[
            "car"
            ] ?? 0
        )
        +
        (
            objectCounts[
            "van"
            ] ?? 0
        )
        +
        (
            objectCounts[
            "truck"
            ] ?? 0
        )
        +
        (
            objectCounts[
            "bus"
            ] ?? 0
        )
        +
        (
            objectCounts[
            "motor"
            ] ?? 0
        )
        +
        (
            objectCounts[
            "motorcycle"
            ] ?? 0
        );


    // ========================================================
    // UI
    // ========================================================

    return (
        <>

            <div className="page-header">

                <h1>
                    Video Analysis
                </h1>

                <p>
                    Upload a surveillance
                    video and run
                    AI-powered detection
                    and tracking.
                </p>

            </div>


            {/* ==================================================
                UPLOAD
            ================================================== */}

            <section className="upload-card">

                <div className="upload-title">
                    Upload Video
                </div>

                <p className="upload-description">
                    Select an MP4, AVI or
                    supported video file.
                </p>


                <div className="upload-row">

                    <label className="file-input">

                        <input
                            type="file"
                            accept="video/*"
                            onChange={
                                handleFileChange
                            }
                        />

                        <span>
                            {file
                                ? file.name
                                : "Choose video"}
                        </span>

                    </label>


                    <button
                        type="button"
                        className="analyze-button"
                        onClick={
                            handleAnalyze
                        }
                        disabled={
                            loading ||
                            deleting ||
                            !file
                        }
                    >
                        {loading
                            ? "Processing..."
                            : "Analyze Video"}
                    </button>

                </div>


                {message && (

                    <div className="info-message">
                        {message}
                    </div>

                )}


                {error && (

                    <div className="error-message">
                        {error}
                    </div>

                )}

            </section>


            {/* ==================================================
                VIDEO STATUS
            ================================================== */}

            {video && (

                <section className="status-card">

                    <div>

                        <strong>
                            {video.filename}
                        </strong>

                        <div className="muted">
                            Video ID:{" "}
                            {video.id}
                        </div>

                    </div>


                    <div
                        style={{
                            display:
                                "flex",
                            alignItems:
                                "center",
                            gap:
                                "12px",
                            flexWrap:
                                "wrap",
                            justifyContent:
                                "flex-end",
                        }}
                    >

                        <div
                            className={`status-badge ${video.status}`}
                        >
                            {video.status}
                        </div>

                        <button
                            type="button"
                            onClick={
                                handleDeleteVideo
                            }
                            disabled={
                                deleting
                            }
                            style={{
                                border:
                                    "none",
                                borderRadius:
                                    "8px",
                                padding:
                                    "10px 16px",
                                background:
                                    deleting
                                        ? "#7f1d1d"
                                        : "#dc2626",
                                color:
                                    "#ffffff",
                                fontWeight:
                                    700,
                                cursor:
                                    deleting
                                        ? "wait"
                                        : "pointer",
                            }}
                        >
                            {deleting
                                ? "Deleting..."
                                : "Delete Video"}
                        </button>

                    </div>

                </section>

            )}


            {/* ==================================================
                REPORT
            ================================================== */}

            {report &&
                video && (

                    <>

                        {/* ==========================================
                            STATISTICS
                        ========================================== */}

                        <section className="stats-grid">

                            <StatCard
                                label="Persons"
                                value={
                                    personCount
                                }
                            />

                            <StatCard
                                label="Vehicles"
                                value={
                                    vehicleCount
                                }
                            />

                            <StatCard
                                label="Unique Tracks"
                                value={
                                    report.tracking
                                        .unique_tracks
                                }
                            />

                            <StatCard
                                label="Total Events"
                                value={
                                    report.totals
                                        .events
                                }
                            />

                            <StatCard
                                label="Critical Alerts"
                                value={
                                    events.filter(
                                        (
                                            event
                                        ) =>
                                            event.severity
                                            === "critical"
                                    ).length
                                }
                            />

                        </section>


                        {/* ==========================================
                            OBJECTS + VIDEO INFO
                        ========================================== */}

                        <section className="content-grid">

                            <div className="panel">

                                <div className="panel-header">

                                    <div>

                                        <h2>
                                            Object Detection
                                        </h2>

                                        <span>
                                            Unique tracked objects
                                        </span>

                                    </div>

                                </div>


                                <div className="object-grid">

                                    {Object.entries(
                                        objectCounts
                                    ).map(
                                        (
                                            [
                                                name,
                                                count,
                                            ]
                                        ) => (

                                            <div
                                                className="object-card"
                                                key={
                                                    name
                                                }
                                            >

                                                <div className="object-name">
                                                    {
                                                        name
                                                    }
                                                </div>

                                                <div className="object-value">
                                                    {
                                                        count
                                                    }
                                                </div>

                                            </div>

                                        )
                                    )}

                                </div>

                            </div>


                            <div className="panel">

                                <div className="panel-header">

                                    <h2>
                                        Video Information
                                    </h2>

                                </div>


                                <InfoRow
                                    label="Duration"
                                    value={`${Number(
                                        report.video
                                            .duration_seconds
                                    ).toFixed(
                                        3
                                    )}s`}
                                />


                                <InfoRow
                                    label="Frames"
                                    value={String(
                                        report.video.frames
                                    )}
                                />


                                <InfoRow
                                    label="FPS"
                                    value={String(
                                        report.video.fps
                                    )}
                                />


                                <InfoRow
                                    label="Unique Tracks"
                                    value={String(
                                        report.tracking
                                            .unique_tracks
                                    )}
                                />


                                <InfoRow
                                    label="Track Observations"
                                    value={String(
                                        report.tracking
                                            .total_track_observations
                                    )}
                                />

                            </div>

                        </section>


                        {/* ==========================================
                            ANALYZED VIDEO
                        ========================================== */}

                        <section className="panel video-panel">

                            <div className="panel-header">

                                <div>

                                    <h2>
                                        Analyzed Video
                                    </h2>

                                    <span>
                                        YOLO detection +
                                        BoT-SORT tracking
                                    </span>

                                </div>

                            </div>


                            <video
                                className="analysis-video"
                                controls
                                src={
                                    api.getAnnotatedVideoUrl(
                                        video.id
                                    )
                                }
                            />

                        </section>


                        {/* ==========================================
                            EVENTS
                        ========================================== */}

                        <section className="panel">

                            <div className="panel-header">

                                <div>

                                    <h2>
                                        Events
                                    </h2>

                                    <span>
                                        {events.length}{" "}
                                        detected
                                    </span>

                                </div>

                            </div>


                            {events.length ===
                                0 ? (

                                <div className="empty">
                                    No events detected.
                                </div>

                            ) : (

                                <div className="event-list">

                                    {events.map(
                                        (
                                            event
                                        ) => (

                                            <div
                                                className="event-row"
                                                key={
                                                    event.id
                                                }
                                            >

                                                <div>

                                                    <strong>
                                                        {
                                                            formatEventName(
                                                                event.event_type
                                                            )
                                                        }
                                                    </strong>

                                                    <div className="muted">

                                                        Track{" "}
                                                        {
                                                            event.track_id ??
                                                            "N/A"
                                                        }

                                                        {" • "}

                                                        {
                                                            Number(
                                                                event.timestamp
                                                            ).toFixed(
                                                                2
                                                            )
                                                        }
                                                        s

                                                    </div>

                                                </div>


                                                <div
                                                    className={`severity ${event.severity}`}
                                                >
                                                    {
                                                        event.severity
                                                    }
                                                </div>

                                            </div>

                                        )
                                    )}

                                </div>

                            )}

                        </section>

                    </>

                )}

        </>
    );
}


// ============================================================
// HELPERS
// ============================================================

function formatEventName(
    value: string
): string {

    return value
        .replace(
            /_/g,
            " "
        )
        .replace(
            /\b\w/g,
            (
                character: string
            ) =>
                character.toUpperCase()
        );
}


function StatCard({
    label,
    value,
}: {
    label: string;
    value: number;
}) {

    return (

        <div className="stat-card">

            <div className="stat-label">
                {label}
            </div>

            <div className="stat-value">
                {
                    Number.isInteger(
                        value
                    )
                        ? value
                        : value.toFixed(
                            2
                        )
                }
            </div>

        </div>

    );
}


function InfoRow({
    label,
    value,
}: {
    label: string;
    value: string;
}) {

    return (

        <div className="info-row">

            <span>
                {label}
            </span>

            <strong>
                {value}
            </strong>

        </div>

    );
}