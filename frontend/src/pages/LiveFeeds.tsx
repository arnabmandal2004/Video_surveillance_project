import LiveDetectionPanel from "../components/LiveDetectionPanel";


export default function LiveFeeds() {

    return (
        <div
            style={{
                padding:
                    "32px",
                maxWidth:
                    "1400px",
                margin:
                    "0 auto",
            }}
        >

            {/* ================================================= */}
            {/* HEADER                                            */}
            {/* ================================================= */}

            <div
                style={{
                    marginBottom:
                        "28px",
                }}
            >

                <h1
                    style={{
                        margin:
                            0,
                        fontSize:
                            "36px",
                        fontWeight:
                            800,
                        color:
                            "#f8fafc",
                    }}
                >
                    Live Feeds
                </h1>

                <p
                    style={{
                        marginTop:
                            "8px",
                        marginBottom:
                            0,
                        color:
                            "#94a3b8",
                        fontSize:
                            "16px",
                    }}
                >
                    Real-time webcam monitoring with
                    AI object detection and threat
                    classification.
                </p>

            </div>


            {/* ================================================= */}
            {/* MODEL INFORMATION                                */}
            {/* ================================================= */}

            <div
                style={{
                    marginBottom:
                        "24px",
                    padding:
                        "16px 18px",
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
                        fontSize:
                            "13px",
                        color:
                            "#94a3b8",
                        marginBottom:
                            "6px",
                    }}
                >
                    LIVE AI MODEL
                </div>

                <div
                    style={{
                        display:
                            "flex",
                        flexWrap:
                            "wrap",
                        gap:
                            "12px 24px",
                        color:
                            "#e2e8f0",
                    }}
                >

                    <span>
                        <strong>
                            YOLO11n
                        </strong>
                        {" "}
                        COCO pretrained model
                    </span>

                    <span>
                        CPU inference
                    </span>

                    <span>
                        Threat policy:
                        {" "}
                        Knife / Scissors
                    </span>

                </div>

            </div>


            {/* ================================================= */}
            {/* LIVE DETECTOR                                    */}
            {/* ================================================= */}

            <LiveDetectionPanel />

        </div>
    );
}