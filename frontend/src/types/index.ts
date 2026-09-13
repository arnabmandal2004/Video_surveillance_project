// ============================================================
// VIDEO
// ============================================================

export interface Video {
    id: number;

    filename: string;

    status:
    | "uploaded"
    | "processing"
    | "completed"
    | "failed";

    annotated_video_path?: string | null;

    uploaded_at: string;
}


// ============================================================
// EVENT
// ============================================================

export interface EventItem {
    id: number;

    event_type: string;

    track_id: number | null;

    timestamp: number;

    severity: string;

    confidence: number;

    message: string | null;
}


// ============================================================
// ALERT
// ============================================================

export interface AlertItem {
    id: number;

    type: string;

    severity: string;

    timestamp: number;

    track_id: number | null;

    status: string;
}


// ============================================================
// ANALYSIS STATUS
// ============================================================

export interface AnalysisStatus {
    video_id: number;

    status: string;

    message?: string | null;
}


// ============================================================
// VIDEO INFORMATION
// ============================================================

export interface VideoInfo {
    frames: number;

    fps: number;

    duration_seconds: number;

    width?: number;

    height?: number;
}


// ============================================================
// TRACKING SUMMARY
// ============================================================

export interface TrackingSummary {
    unique_tracks: number;

    total_track_observations: number;
}


// ============================================================
// OBJECT SUMMARY
// ============================================================

export interface ObjectSummary {
    unique_objects_by_class: Record<
        string,
        number
    >;

    track_observations_by_class: Record<
        string,
        number
    >;
}


// ============================================================
// ANALYSIS TOTALS
// ============================================================

export interface AnalysisTotals {
    unique_object_tracks: number;

    track_observations: number;

    events: number;
}


// ============================================================
// ANALYSIS REPORT
// ============================================================

export interface AnalysisReport {
    video_id: number;

    filename: string;

    status: string;

    video: VideoInfo;

    tracking: TrackingSummary;

    objects: ObjectSummary;

    events: Record<
        string,
        number
    >;

    totals: AnalysisTotals;

    summary?: {
        persons: number;

        vehicles: number;
    };

    annotated_video_url?: string | null;

    report_url?: string | null;

    events_url?: string | null;
}


// ============================================================
// LIVE DETECTION
// ============================================================

export interface LiveDetection {
    class_id: number;

    class_name: string;

    display_name: string;

    confidence: number;

    bbox: [
        number,
        number,
        number,
        number
    ];

    is_threat: boolean;

    threat_level:
    | "NONE"
    | "SAFE"
    | "LOW"
    | "MEDIUM"
    | "HIGH";

    message: string;
}


// ============================================================
// LIVE THREAT ALERT
// ============================================================

export interface LiveThreatAlert {
    triggered: boolean;

    object: string;

    threat_level:
    | "LOW"
    | "MEDIUM"
    | "HIGH";

    confidence: number;

    snapshot_url: string;

    filename: string;

    created_at: string;

    message: string;
}


// ============================================================
// LIVE DETECTION RESPONSE
// ============================================================

export interface LiveDetectionResponse {
    width: number;

    height: number;

    detections: LiveDetection[];

    threat_count: number;

    highest_threat:
    | "SAFE"
    | "LOW"
    | "MEDIUM"
    | "HIGH";

    threat_alert:
    | LiveThreatAlert
    | null;
}