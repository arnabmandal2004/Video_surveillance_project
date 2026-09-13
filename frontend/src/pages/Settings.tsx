export default function Settings() {
    return (
        <>
            <div className="page-header">
                <h1>Settings</h1>
                <p>
                    SentinelAI detection and analysis
                    configuration.
                </p>
            </div>

            <section className="panel">
                <div className="panel-header">
                    <h2>AI Configuration</h2>
                </div>

                <div className="info-row">
                    <span>Detection Model</span>
                    <strong>
                        SentinelAI VisDrone YOLO11n
                    </strong>
                </div>

                <div className="info-row">
                    <span>Tracker</span>
                    <strong>BoT-SORT</strong>
                </div>

                <div className="info-row">
                    <span>Device</span>
                    <strong>CPU</strong>
                </div>

                <div className="info-row">
                    <span>Restricted Zone</span>
                    <strong>
                        Configurable
                    </strong>
                </div>

                <div className="info-row">
                    <span>Loitering Detection</span>
                    <strong>Enabled</strong>
                </div>
            </section>
        </>
    );
}