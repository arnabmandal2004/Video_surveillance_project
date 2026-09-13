import { useEffect, useState } from "react";
import { api } from "../services/api";
import { AnalysisReport } from "../types";

export default function Analytics() {
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

    if (!report) {
        return (
            <>
                <div className="page-header">
                    <h1>Analytics</h1>
                    <p>
                        Statistical analysis of the latest
                        processed video.
                    </p>
                </div>

                <section className="panel">
                    <div className="empty">
                        Analyze a video first to display
                        analytics.
                    </div>
                </section>
            </>
        );
    }

    return (
        <>
            <div className="page-header">
                <h1>Analytics</h1>
                <p>
                    Object, tracking and event statistics.
                </p>
            </div>

            <section className="stats-grid">
                <Stat
                    label="Unique Tracks"
                    value={
                        report.tracking.unique_tracks
                    }
                />

                <Stat
                    label="Track Observations"
                    value={
                        report.tracking
                            .total_track_observations
                    }
                />

                <Stat
                    label="Frames"
                    value={report.video.frames}
                />

                <Stat
                    label="FPS"
                    value={report.video.fps}
                />

                <Stat
                    label="Events"
                    value={report.totals.events}
                />
            </section>

            <section className="panel">
                <div className="panel-header">
                    <h2>
                        Objects by Class
                    </h2>
                </div>

                {Object.entries(
                    report.objects
                        .unique_objects_by_class
                ).map(([name, count]) => (
                    <div
                        className="info-row"
                        key={name}
                    >
                        <span>{name}</span>
                        <strong>{count}</strong>
                    </div>
                ))}
            </section>

            <section className="panel">
                <div className="panel-header">
                    <h2>Events by Type</h2>
                </div>

                {Object.entries(report.events)
                    .length === 0 ? (
                    <div className="empty">
                        No events detected.
                    </div>
                ) : (
                    Object.entries(
                        report.events
                    ).map(([name, count]) => (
                        <div
                            className="info-row"
                            key={name}
                        >
                            <span>{name}</span>
                            <strong>{count}</strong>
                        </div>
                    ))
                )}
            </section>
        </>
    );
}

function Stat({
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