import { useEffect, useState } from "react";
import { api } from "../services/api";
import {
    AlertItem,
    AnalysisReport,
    EventItem,
    Video,
} from "../types";

export default function Dashboard() {
    const [video, setVideo] = useState<Video | null>(null);
    const [report, setReport] = useState<AnalysisReport | null>(null);
    const [events, setEvents] = useState<EventItem[]>([]);
    const [alerts, setAlerts] = useState<AlertItem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadDashboard();
    }, []);

    async function loadDashboard() {
        try {
            setLoading(true);

            const savedId = localStorage.getItem(
                "sentinelai_last_video_id"
            );

            const alertsData = await api.getAlerts();
            setAlerts(alertsData);

            if (!savedId) {
                setLoading(false);
                return;
            }

            const videoId = Number(savedId);

            if (!Number.isInteger(videoId) || videoId <= 0) {
                setLoading(false);
                return;
            }

            const videoData = await api.getVideo(videoId);
            setVideo(videoData);

            if (videoData.status === "completed") {
                const [reportData, eventData] =
                    await Promise.all([
                        api.getVideoReport(videoId),
                        api.getVideoEvents(videoId),
                    ]);

                setReport(reportData);
                setEvents(eventData);
            }
        } catch (error) {
            console.error(
                "Dashboard loading failed:",
                error
            );
        } finally {
            setLoading(false);
        }
    }

    const objectCounts =
        report?.objects?.unique_objects_by_class ?? {};

    const persons =
        (objectCounts["pedestrian"] ?? 0) +
        (objectCounts["people"] ?? 0);

    const vehicles =
        (objectCounts["car"] ?? 0) +
        (objectCounts["van"] ?? 0) +
        (objectCounts["truck"] ?? 0) +
        (objectCounts["bus"] ?? 0) +
        (objectCounts["motor"] ?? 0) +
        (objectCounts["bicycle"] ?? 0) +
        (objectCounts["tricycle"] ?? 0) +
        (objectCounts["awning-tricycle"] ?? 0);

    const uniqueTracks =
        report?.tracking?.unique_tracks ?? 0;

    const totalEvents =
        report?.totals?.events ?? events.length;

    const criticalAlerts = events.filter(
        (event) => event.severity === "critical"
    ).length;

    const formatName = (value: string) => {
        return value
            .replace(/_/g, " ")
            .replace(
                /\b\w/g,
                (char: string) =>
                    char.toUpperCase()
            );
    };

    return (
        <>
            <div className="page-header">
                <div>
                    <h1>Dashboard</h1>

                    <p>
                        SentinelAI surveillance overview
                        and latest analysis.
                    </p>
                </div>
            </div>

            {loading ? (
                <section className="panel">
                    <div className="empty">
                        Loading latest analysis...
                    </div>
                </section>
            ) : !report ? (
                <section className="panel">
                    <div className="panel-header">
                        <h2>No Analysis Yet</h2>
                    </div>

                    <div className="empty">
                        Go to Video Analysis to upload
                        and analyze a video.
                    </div>
                </section>
            ) : (
                <>
                    {/* Latest analysis */}
                    <section className="status-card">
                        <div>
                            <strong>
                                {video?.filename}
                            </strong>

                            <div className="muted">
                                Latest analyzed video
                                {" • "}
                                ID {video?.id}
                            </div>
                        </div>

                        <div className="status-badge completed">
                            COMPLETED
                        </div>
                    </section>

                    {/* Summary statistics */}
                    <section className="stats-grid">
                        <StatCard
                            label="Persons"
                            value={persons}
                        />

                        <StatCard
                            label="Vehicles"
                            value={vehicles}
                        />

                        <StatCard
                            label="Unique Tracks"
                            value={uniqueTracks}
                        />

                        <StatCard
                            label="Total Events"
                            value={totalEvents}
                        />

                        <StatCard
                            label="Critical Alerts"
                            value={criticalAlerts}
                        />
                    </section>

                    {/* Two-column overview */}
                    <section className="content-grid">
                        <div className="panel">
                            <div className="panel-header">
                                <h2>
                                    Object Summary
                                </h2>

                                <span>
                                    Unique tracked objects
                                </span>
                            </div>

                            <div className="object-grid">
                                {Object.entries(
                                    objectCounts
                                ).map(
                                    ([name, count]) => (
                                        <div
                                            className="object-card"
                                            key={name}
                                        >
                                            <div className="object-name">
                                                {formatName(
                                                    name
                                                )}
                                            </div>

                                            <div className="object-value">
                                                {count}
                                            </div>
                                        </div>
                                    )
                                )}
                            </div>
                        </div>

                        <div className="panel">
                            <div className="panel-header">
                                <h2>
                                    Video Summary
                                </h2>
                            </div>

                            <InfoRow
                                label="Duration"
                                value={`${report.video.duration_seconds}s`}
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
                        </div>
                    </section>

                    {/* Recent alerts */}
                    <section className="panel">
                        <div className="panel-header">
                            <h2>
                                Recent Alerts
                            </h2>

                            <span>
                                {alerts.length} total
                            </span>
                        </div>

                        {alerts.length === 0 ? (
                            <div className="empty">
                                No alerts recorded.
                            </div>
                        ) : (
                            <div className="event-list">
                                {alerts
                                    .slice(0, 8)
                                    .map((alert) => (
                                        <div
                                            className="event-row"
                                            key={alert.id}
                                        >
                                            <div>
                                                <strong>
                                                    {formatName(
                                                        alert.type
                                                    )}
                                                </strong>

                                                <div className="muted">
                                                    Track{" "}
                                                    {alert.track_id ??
                                                        "N/A"}
                                                    {" • "}
                                                    {alert.timestamp.toFixed(
                                                        2
                                                    )}
                                                    s
                                                </div>
                                            </div>

                                            <div
                                                className={`severity ${alert.severity}`}
                                            >
                                                {
                                                    alert.severity
                                                }
                                            </div>
                                        </div>
                                    ))}
                            </div>
                        )}
                    </section>

                    {/* Recent events */}
                    <section className="panel">
                        <div className="panel-header">
                            <h2>
                                Latest Events
                            </h2>

                            <span>
                                {events.length} detected
                            </span>
                        </div>

                        {events.length === 0 ? (
                            <div className="empty">
                                No events detected in the
                                latest analysis.
                            </div>
                        ) : (
                            <div className="event-list">
                                {events
                                    .slice(0, 5)
                                    .map((event) => (
                                        <div
                                            className="event-row"
                                            key={event.id}
                                        >
                                            <div>
                                                <strong>
                                                    {formatName(
                                                        event.event_type
                                                    )}
                                                </strong>

                                                <div className="muted">
                                                    Track{" "}
                                                    {event.track_id ??
                                                        "N/A"}
                                                    {" • "}
                                                    {event.timestamp.toFixed(
                                                        2
                                                    )}
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
                                    ))}
                            </div>
                        )}
                    </section>
                </>
            )}
        </>
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
                {value}
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
            <span>{label}</span>

            <strong>{value}</strong>
        </div>
    );
}