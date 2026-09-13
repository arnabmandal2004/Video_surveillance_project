import { useEffect, useState } from "react";
import { api } from "../services/api";
import { EventItem } from "../types";

export default function Alerts() {
    const [events, setEvents] = useState<EventItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [videoId, setVideoId] = useState<number | null>(null);
    const [error, setError] = useState("");

    useEffect(() => {
        loadAlerts();
    }, []);

    async function loadAlerts() {
        try {
            setLoading(true);
            setError("");

            const savedId = localStorage.getItem(
                "sentinelai_last_video_id"
            );

            if (!savedId) {
                setVideoId(null);
                setEvents([]);
                return;
            }

            const id = Number(savedId);

            if (!Number.isInteger(id) || id <= 0) {
                localStorage.removeItem(
                    "sentinelai_last_video_id"
                );

                setVideoId(null);
                setEvents([]);
                return;
            }

            setVideoId(id);

            // Get events ONLY for the current video.
            const videoEvents =
                await api.getVideoEvents(id);

            // Alerts are currently represented by
            // critical/warning events.
            const alertEvents = videoEvents.filter(
                (event) =>
                    event.severity === "critical" ||
                    event.severity === "warning"
            );

            setEvents(alertEvents);
        } catch (err) {
            console.error(err);

            setError(
                err instanceof Error
                    ? err.message
                    : "Could not load alerts."
            );
        } finally {
            setLoading(false);
        }
    }

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
                <h1>Alerts</h1>

                <p>
                    Security alerts for the latest analyzed video.
                </p>
            </div>

            <section className="panel">
                <div className="panel-header">
                    <h2>Current Video Alerts</h2>

                    <span>
                        {events.length} alerts
                    </span>
                </div>

                {loading && (
                    <div className="empty">
                        Loading alerts...
                    </div>
                )}

                {!loading && error && (
                    <div className="error-message">
                        {error}
                    </div>
                )}

                {!loading &&
                    !error &&
                    !videoId && (
                        <div className="empty">
                            Analyze a video first.
                        </div>
                    )}

                {!loading &&
                    !error &&
                    videoId &&
                    events.length === 0 && (
                        <div className="empty">
                            No alerts detected for the
                            latest video.
                        </div>
                    )}

                {!loading &&
                    !error &&
                    events.length > 0 && (
                        <div className="event-list">
                            {events.map((event) => (
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
                                        {event.severity}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
            </section>
        </>
    );
}