import { useEffect, useState } from "react";
import { api } from "../services/api";
import { AnalysisReport } from "../types";

export default function Reports() {
    const [report, setReport] =
        useState<AnalysisReport | null>(null);

    useEffect(() => {
        const savedId = localStorage.getItem(
            "sentinelai_last_video_id"
        );

        if (!savedId) {
            return;
        }

        api.getVideoReport(Number(savedId))
            .then(setReport)
            .catch(console.error);
    }, []);

    return (
        <>
            <div className="page-header">
                <h1>Reports</h1>
                <p>
                    Generated analysis reports and outputs.
                </p>
            </div>

            {!report ? (
                <section className="panel">
                    <div className="empty">
                        No generated report available.
                        Analyze a video first.
                    </div>
                </section>
            ) : (
                <>
                    <section className="panel">
                        <div className="panel-header">
                            <div>
                                <h2>
                                    {report.filename}
                                </h2>

                                <span>
                                    Analysis completed
                                </span>
                            </div>

                            <div className="button-group">
                                <a
                                    className="secondary-button"
                                    href={api.getReportUrl(
                                        report.video_id
                                    )}
                                    target="_blank"
                                    rel="noreferrer"
                                >
                                    View JSON
                                </a>

                                <a
                                    className="secondary-button"
                                    href={api.getReportUrl(
                                        report.video_id
                                    )}
                                    download
                                >
                                    Download Report
                                </a>
                            </div>
                        </div>

                        <div className="info-row">
                            <span>Duration</span>
                            <strong>
                                {
                                    report.video
                                        .duration_seconds
                                }
                                s
                            </strong>
                        </div>

                        <div className="info-row">
                            <span>Frames</span>
                            <strong>
                                {report.video.frames}
                            </strong>
                        </div>

                        <div className="info-row">
                            <span>Unique Tracks</span>
                            <strong>
                                {
                                    report.tracking
                                        .unique_tracks
                                }
                            </strong>
                        </div>

                        <div className="info-row">
                            <span>Total Events</span>
                            <strong>
                                {report.totals.events}
                            </strong>
                        </div>
                    </section>

                    <section className="panel">
                        <div className="panel-header">
                            <h2>
                                Annotated Video
                            </h2>
                        </div>

                        <video
                            className="analysis-video"
                            controls
                            src={api.getAnnotatedVideoUrl(
                                report.video_id
                            )}
                        />
                    </section>
                </>
            )}
        </>
    );
}