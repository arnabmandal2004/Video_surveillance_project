import {
    useEffect,
    useRef,
    useState,
} from "react";

import { api } from "../services/api";

import {
    LiveDetection,
    LiveThreatAlert,
} from "../types";


const DETECTION_INTERVAL_MS = 500;


export default function LiveDetectionPanel() {

    // ========================================================
    // REFS
    // ========================================================

    const videoRef =
        useRef<HTMLVideoElement | null>(
            null
        );

    const overlayCanvasRef =
        useRef<HTMLCanvasElement | null>(
            null
        );

    const captureCanvasRef =
        useRef<HTMLCanvasElement | null>(
            null
        );

    const streamRef =
        useRef<MediaStream | null>(
            null
        );

    const timerRef =
        useRef<number | null>(
            null
        );

    const detectingRef =
        useRef(false);


    // ========================================================
    // STATE
    // ========================================================

    const [
        cameraRunning,
        setCameraRunning,
    ] = useState(false);

    const [
        detections,
        setDetections,
    ] = useState<LiveDetection[]>([]);

    const [
        error,
        setError,
    ] = useState("");

    const [
        lastDetectionTime,
        setLastDetectionTime,
    ] = useState("");

    const [
        cameraLoading,
        setCameraLoading,
    ] = useState(false);

    const [
        threatAlert,
        setThreatAlert,
    ] = useState<LiveThreatAlert | null>(
        null
    );

    const [
        alertVisible,
        setAlertVisible,
    ] = useState(false);


    // ========================================================
    // START CAMERA
    // ========================================================

    async function startCamera() {

        setError("");
        setCameraLoading(true);

        try {

            if (
                !navigator.mediaDevices ||
                !navigator.mediaDevices.getUserMedia
            ) {

                throw new Error(
                    "Webcam access is not supported by this browser."
                );
            }

            const stream =
                await navigator.mediaDevices.getUserMedia(
                    {
                        video: {
                            width: {
                                ideal: 1280,
                            },
                            height: {
                                ideal: 720,
                            },
                            facingMode: "user",
                        },
                        audio: false,
                    }
                );

            streamRef.current =
                stream;

            const video =
                videoRef.current;

            if (!video) {

                throw new Error(
                    "Video element is unavailable."
                );
            }

            video.srcObject =
                stream;

            await video.play();

            setCameraRunning(true);

        } catch (err) {

            console.error(err);

            setError(
                err instanceof Error
                    ? err.message
                    : "Unable to access webcam."
            );

        } finally {

            setCameraLoading(false);
        }
    }


    // ========================================================
    // STOP CAMERA
    // ========================================================

    function stopCamera() {

        if (
            timerRef.current !== null
        ) {

            window.clearInterval(
                timerRef.current
            );

            timerRef.current =
                null;
        }

        detectingRef.current =
            false;

        if (streamRef.current) {

            streamRef.current
                .getTracks()
                .forEach(
                    (track) =>
                        track.stop()
                );

            streamRef.current =
                null;
        }

        const video =
            videoRef.current;

        if (video) {

            video.pause();

            video.srcObject =
                null;
        }

        setCameraRunning(false);

        setDetections([]);

        setThreatAlert(null);

        setAlertVisible(false);

        clearOverlay();
    }


    // ========================================================
    // CLEANUP
    // ========================================================

    useEffect(() => {

        return () => {

            if (
                timerRef.current !== null
            ) {

                window.clearInterval(
                    timerRef.current
                );
            }

            if (streamRef.current) {

                streamRef.current
                    .getTracks()
                    .forEach(
                        (track) =>
                            track.stop()
                    );
            }
        };

    }, []);


    // ========================================================
    // DETECTION LOOP
    // ========================================================

    useEffect(() => {

        if (!cameraRunning) {
            return;
        }

        timerRef.current =
            window.setInterval(
                () => {
                    void detectCurrentFrame();
                },
                DETECTION_INTERVAL_MS
            );

        return () => {

            if (
                timerRef.current !== null
            ) {

                window.clearInterval(
                    timerRef.current
                );

                timerRef.current =
                    null;
            }
        };

    }, [cameraRunning]);


    // ========================================================
    // DETECT CURRENT FRAME
    // ========================================================

    async function detectCurrentFrame() {

        if (
            detectingRef.current
        ) {
            return;
        }

        const video =
            videoRef.current;

        const captureCanvas =
            captureCanvasRef.current;

        if (
            !video ||
            !captureCanvas ||
            video.readyState <
            HTMLMediaElement.HAVE_CURRENT_DATA
        ) {
            return;
        }

        if (
            video.videoWidth === 0 ||
            video.videoHeight === 0
        ) {
            return;
        }

        detectingRef.current =
            true;

        try {

            captureCanvas.width =
                video.videoWidth;

            captureCanvas.height =
                video.videoHeight;

            const context =
                captureCanvas.getContext(
                    "2d"
                );

            if (!context) {
                return;
            }

            context.drawImage(
                video,
                0,
                0,
                captureCanvas.width,
                captureCanvas.height
            );


            const blob =
                await new Promise<Blob | null>(
                    (resolve) => {

                        captureCanvas.toBlob(
                            resolve,
                            "image/jpeg",
                            0.78
                        );
                    }
                );


            if (!blob) {
                return;
            }


            const result =
                await api.detectLiveFrame(
                    blob
                );


            setDetections(
                result.detections
            );


            setLastDetectionTime(
                new Date().toLocaleTimeString()
            );


            drawDetections(
                result.detections,
                result.width,
                result.height
            );


            // ------------------------------------------------
            // THREAT ALERT
            // ------------------------------------------------

            if (
                result.threat_alert
            ) {

                const newAlert =
                    result.threat_alert;

                setThreatAlert(
                    newAlert
                );

                setAlertVisible(
                    true
                );


                /*
                 * Automatically hide the visible alert
                 * after 4 seconds.
                 *
                 * The screenshot remains available.
                 */
                window.setTimeout(
                    () => {
                        setAlertVisible(
                            false
                        );
                    },
                    4000
                );
            }

        } catch (err) {

            console.error(err);

            setError(
                err instanceof Error
                    ? err.message
                    : "Live detection failed."
            );

        } finally {

            detectingRef.current =
                false;
        }
    }


    // ========================================================
    // DRAW DETECTIONS
    // ========================================================

    function drawDetections(
        items: LiveDetection[],
        sourceWidth: number,
        sourceHeight: number
    ) {

        const canvas =
            overlayCanvasRef.current;

        if (!canvas) {
            return;
        }

        canvas.width =
            sourceWidth;

        canvas.height =
            sourceHeight;


        const context =
            canvas.getContext(
                "2d"
            );

        if (!context) {
            return;
        }


        context.clearRect(
            0,
            0,
            sourceWidth,
            sourceHeight
        );


        for (
            const detection
            of items
        ) {

            const [
                x1,
                y1,
                x2,
                y2,
            ] = detection.bbox;


            const isThreat =
                detection.is_threat;


            context.lineWidth =
                isThreat
                    ? 5
                    : 4;


            context.strokeStyle =
                isThreat
                    ? "#ff2d2d"
                    : "#36e27b";


            context.strokeRect(
                x1,
                y1,
                x2 - x1,
                y2 - y1
            );


            const label =
                isThreat
                    ? `${detection.display_name} • THREAT • ${(
                        detection.confidence *
                        100
                    ).toFixed(0)}%`
                    : `${detection.display_name} • SAFE • ${(
                        detection.confidence *
                        100
                    ).toFixed(0)}%`;


            context.font =
                "bold 18px Arial";


            const metrics =
                context.measureText(
                    label
                );


            const labelWidth =
                metrics.width +
                16;


            const labelHeight =
                30;


            const labelY =
                Math.max(
                    0,
                    y1 -
                    labelHeight
                );


            context.fillStyle =
                isThreat
                    ? "rgba(220, 30, 30, 0.95)"
                    : "rgba(20, 120, 65, 0.90)";


            context.fillRect(
                x1,
                labelY,
                labelWidth,
                labelHeight
            );


            context.fillStyle =
                "#ffffff";


            context.fillText(
                label,
                x1 + 8,
                labelY + 21
            );
        }
    }


    // ========================================================
    // CLEAR OVERLAY
    // ========================================================

    function clearOverlay() {

        const canvas =
            overlayCanvasRef.current;

        if (!canvas) {
            return;
        }

        const context =
            canvas.getContext(
                "2d"
            );

        if (!context) {
            return;
        }

        context.clearRect(
            0,
            0,
            canvas.width,
            canvas.height
        );
    }


    // ========================================================
    // SUMMARY
    // ========================================================

    const threatCount =
        detections.filter(
            (item) =>
                item.is_threat
        ).length;


    const highestThreat =
        detections.some(
            (item) =>
                item.threat_level ===
                "HIGH"
        )
            ? "HIGH"
            : detections.some(
                (item) =>
                    item.is_threat
            )
                ? "THREAT"
                : "SAFE";


    // ========================================================
    // RENDER
    // ========================================================

    return (

        <div
            style={{
                display:
                    "grid",
                gap:
                    "20px",
            }}
        >

            {/* ================================================= */}
            {/* THREAT ALERT                                     */}
            {/* ================================================= */}

            {alertVisible &&
                threatAlert && (

                    <div
                        style={{
                            padding:
                                "18px 20px",
                            borderRadius:
                                "14px",
                            background:
                                "linear-gradient(135deg, rgba(127,29,29,0.95), rgba(185,28,28,0.88))",
                            border:
                                "2px solid rgba(248,113,113,0.8)",
                            boxShadow:
                                "0 12px 35px rgba(220,38,38,0.25)",
                            color:
                                "#ffffff",
                            display:
                                "flex",
                            flexWrap:
                                "wrap",
                            alignItems:
                                "center",
                            justifyContent:
                                "space-between",
                            gap:
                                "16px",
                        }}
                    >

                        <div>

                            <div
                                style={{
                                    fontSize:
                                        "24px",
                                    fontWeight:
                                        900,
                                    marginBottom:
                                        "6px",
                                }}
                            >
                                🚨 THREAT DETECTED
                            </div>

                            <div
                                style={{
                                    fontSize:
                                        "15px",
                                }}
                            >
                                {threatAlert.object.toUpperCase()}
                                {" • "}
                                {threatAlert.threat_level}
                                {" • "}
                                {(threatAlert.confidence * 100).toFixed(0)}
                                %
                            </div>

                            <div
                                style={{
                                    marginTop:
                                        "6px",
                                    fontSize:
                                        "13px",
                                    opacity:
                                        0.9,
                                }}
                            >
                                Screenshot automatically saved.
                            </div>

                        </div>


                        <a
                            href={
                                `${(
                                    import.meta.env.VITE_API_BASE ||
                                    "http://localhost:8000"
                                ).replace(/\/$/, "")}${threatAlert.snapshot_url}`
                            }
                            target="_blank"
                            rel="noreferrer"
                            style={{
                                display:
                                    "inline-flex",
                                alignItems:
                                    "center",
                                textDecoration:
                                    "none",
                                padding:
                                    "11px 16px",
                                borderRadius:
                                    "9px",
                                background:
                                    "#ffffff",
                                color:
                                    "#991b1b",
                                fontWeight:
                                    800,
                            }}
                        >
                            📸 View Snapshot
                        </a>

                    </div>
                )
            }


            {/* ================================================= */}
            {/* CONTROLS                                         */}
            {/* ================================================= */}

            <div
                style={{
                    display:
                        "flex",
                    flexWrap:
                        "wrap",
                    gap:
                        "12px",
                    alignItems:
                        "center",
                }}
            >

                {!cameraRunning ? (

                    <button
                        onClick={
                            startCamera
                        }
                        disabled={
                            cameraLoading
                        }
                        style={{
                            border:
                                "none",
                            borderRadius:
                                "10px",
                            padding:
                                "12px 20px",
                            fontWeight:
                                700,
                            cursor:
                                cameraLoading
                                    ? "wait"
                                    : "pointer",
                            background:
                                "#2563eb",
                            color:
                                "#ffffff",
                        }}
                    >
                        {cameraLoading
                            ? "Starting Camera..."
                            : "Start Camera"}
                    </button>

                ) : (

                    <button
                        onClick={
                            stopCamera
                        }
                        style={{
                            border:
                                "none",
                            borderRadius:
                                "10px",
                            padding:
                                "12px 20px",
                            fontWeight:
                                700,
                            cursor:
                                "pointer",
                            background:
                                "#dc2626",
                            color:
                                "#ffffff",
                        }}
                    >
                        Stop Camera
                    </button>
                )}


                <span
                    style={{
                        fontSize:
                            "14px",
                        color:
                            cameraRunning
                                ? "#36e27b"
                                : "#94a3b8",
                    }}
                >
                    {cameraRunning
                        ? "● Camera Active"
                        : "● Camera Off"}
                </span>

            </div>


            {/* ================================================= */}
            {/* ERROR                                             */}
            {/* ================================================= */}

            {error && (

                <div
                    style={{
                        padding:
                            "12px 14px",
                        borderRadius:
                            "10px",
                        background:
                            "rgba(220,38,38,0.12)",
                        border:
                            "1px solid rgba(220,38,38,0.35)",
                        color:
                            "#fca5a5",
                    }}
                >
                    {error}
                </div>
            )}


            {/* ================================================= */}
            {/* CAMERA                                            */}
            {/* ================================================= */}

            <div
                style={{
                    position:
                        "relative",
                    width:
                        "100%",
                    maxWidth:
                        "1100px",
                    aspectRatio:
                        "16 / 9",
                    borderRadius:
                        "16px",
                    overflow:
                        "hidden",
                    background:
                        "#050912",
                    border:
                        "1px solid rgba(148,163,184,0.15)",
                }}
            >

                <video
                    ref={
                        videoRef
                    }
                    muted
                    playsInline
                    autoPlay
                    style={{
                        width:
                            "100%",
                        height:
                            "100%",
                        objectFit:
                            "cover",
                        display:
                            "block",
                        transform: "scaleX(-1)",
                    }}
                />


                <canvas
                    ref={
                        overlayCanvasRef
                    }
                    style={{
                        position:
                            "absolute",
                        inset:
                            0,
                        width:
                            "100%",
                        height:
                            "100%",
                        pointerEvents:
                            "none",
                    }}
                />


                <canvas
                    ref={
                        captureCanvasRef
                    }
                    style={{
                        display:
                            "none",
                    }}
                />


                {!cameraRunning && (

                    <div
                        style={{
                            position:
                                "absolute",
                            inset:
                                0,
                            display:
                                "flex",
                            alignItems:
                                "center",
                            justifyContent:
                                "center",
                            color:
                                "#64748b",
                            fontSize:
                                "18px",
                            textAlign:
                                "center",
                            padding:
                                "20px",
                        }}
                    >
                        Click "Start Camera" to begin
                        live AI threat detection.
                    </div>
                )}

            </div>


            {/* ================================================= */}
            {/* STATUS CARDS                                      */}
            {/* ================================================= */}

            <div
                style={{
                    display:
                        "grid",
                    gridTemplateColumns:
                        "repeat(auto-fit, minmax(180px, 1fr))",
                    gap:
                        "14px",
                }}
            >

                <StatusCard
                    label="Detected Objects"
                    value={
                        detections.length
                    }
                />


                <StatusCard
                    label="Threats"
                    value={
                        threatCount
                    }
                    danger={
                        threatCount >
                        0
                    }
                />


                <StatusCard
                    label="Threat Level"
                    value={
                        highestThreat
                    }
                    danger={
                        highestThreat !==
                        "SAFE"
                    }
                />


                <StatusCard
                    label="Last Scan"
                    value={
                        lastDetectionTime ||
                        "Waiting"
                    }
                />

            </div>


            {/* ================================================= */}
            {/* LAST SAVED SNAPSHOT                               */}
            {/* ================================================= */}

            {threatAlert && (

                <section
                    style={{
                        padding:
                            "18px",
                        borderRadius:
                            "14px",
                        background:
                            "#0b111d",
                        border:
                            "1px solid rgba(239,68,68,0.25)",
                    }}
                >

                    <div
                        style={{
                            display:
                                "flex",
                            alignItems:
                                "center",
                            justifyContent:
                                "space-between",
                            gap:
                                "12px",
                            flexWrap:
                                "wrap",
                            marginBottom:
                                "12px",
                        }}
                    >

                        <div>

                            <h3
                                style={{
                                    margin:
                                        0,
                                    fontSize:
                                        "18px",
                                }}
                            >
                                Latest Threat Snapshot
                            </h3>

                            <div
                                style={{
                                    marginTop:
                                        "5px",
                                    color:
                                        "#94a3b8",
                                    fontSize:
                                        "13px",
                                }}
                            >
                                {threatAlert.object}
                                {" • "}
                                {threatAlert.threat_level}
                                {" • "}
                                {(threatAlert.confidence * 100).toFixed(1)}
                                %
                            </div>

                        </div>


                        <a
                            href={
                                `${(
                                    import.meta.env.VITE_API_BASE ||
                                    "http://localhost:8000"
                                ).replace(/\/$/, "")}${threatAlert.snapshot_url}`
                            }
                            target="_blank"
                            rel="noreferrer"
                            style={{
                                color:
                                    "#93c5fd",
                                fontWeight:
                                    700,
                                textDecoration:
                                    "none",
                            }}
                        >
                            Open Full Image
                        </a>

                    </div>


                    <img
                        src={
                            `${(
                                import.meta.env.VITE_API_BASE ||
                                "http://localhost:8000"
                            ).replace(/\/$/, "")}${threatAlert.snapshot_url}`
                        }
                        alt="Latest threat snapshot"
                        style={{
                            width:
                                "100%",
                            maxWidth:
                                "700px",
                            maxHeight:
                                "450px",
                            objectFit:
                                "contain",
                            borderRadius:
                                "10px",
                            display:
                                "block",
                            background:
                                "#050912",
                        }}
                    />

                </section>
            )}


            {/* ================================================= */}
            {/* DETECTION RESULTS                                */}
            {/* ================================================= */}

            <div
                style={{
                    display:
                        "grid",
                    gap:
                        "10px",
                }}
            >

                <h3
                    style={{
                        margin:
                            0,
                        fontSize:
                            "18px",
                    }}
                >
                    Live Detection Results
                </h3>


                {detections.length ===
                    0 ? (

                    <div
                        style={{
                            padding:
                                "18px",
                            borderRadius:
                                "12px",
                            background:
                                "#0b111d",
                            color:
                                "#94a3b8",
                        }}
                    >
                        No objects detected in
                        the latest frame.
                    </div>

                ) : (

                    detections.map(
                        (
                            detection,
                            index
                        ) => (

                            <div
                                key={
                                    `${detection.class_name}-${index}`
                                }
                                style={{
                                    display:
                                        "flex",
                                    alignItems:
                                        "center",
                                    justifyContent:
                                        "space-between",
                                    gap:
                                        "14px",
                                    padding:
                                        "14px 16px",
                                    borderRadius:
                                        "12px",
                                    background:
                                        "#0b111d",
                                    border:
                                        detection.is_threat
                                            ? "1px solid rgba(239,68,68,0.5)"
                                            : "1px solid rgba(54,226,123,0.25)",
                                }}
                            >

                                <div>

                                    <div
                                        style={{
                                            fontWeight:
                                                700,
                                        }}
                                    >
                                        {
                                            detection.display_name
                                        }
                                    </div>

                                    <div
                                        style={{
                                            fontSize:
                                                "13px",
                                            color:
                                                "#94a3b8",
                                            marginTop:
                                                "4px",
                                        }}
                                    >
                                        Confidence:{" "}
                                        {(
                                            detection.confidence *
                                            100
                                        ).toFixed(1)}
                                        %
                                    </div>

                                </div>


                                <div
                                    style={{
                                        fontWeight:
                                            800,
                                        color:
                                            detection.is_threat
                                                ? "#f87171"
                                                : "#36e27b",
                                    }}
                                >
                                    {detection.is_threat
                                        ? `THREAT • ${detection.threat_level}`
                                        : "SAFE"}
                                </div>

                            </div>
                        )
                    )
                )}

            </div>

        </div>
    );
}


// ============================================================
// STATUS CARD
// ============================================================

function StatusCard(
    props: {
        label: string;
        value: string | number;
        danger?: boolean;
    }
) {

    return (

        <div
            style={{
                padding:
                    "16px",
                borderRadius:
                    "12px",
                background:
                    "#0b111d",
                border:
                    "1px solid rgba(148,163,184,0.12)",
            }}
        >

            <div
                style={{
                    color:
                        "#94a3b8",
                    fontSize:
                        "13px",
                    marginBottom:
                        "8px",
                }}
            >
                {props.label}
            </div>


            <div
                style={{
                    fontSize:
                        "22px",
                    fontWeight:
                        800,
                    color:
                        props.danger
                            ? "#f87171"
                            : "#f8fafc",
                }}
            >
                {props.value}
            </div>

        </div>
    );
}