import {
    Video,
    EventItem,
    AlertItem,
    AnalysisReport,
    AnalysisStatus,
    LiveDetectionResponse,
} from "../types";


const API_BASE =
    (
        import.meta.env.VITE_API_BASE ||
        "http://localhost:8000"
    ).replace(/\/$/, "");


async function request<T>(
    path: string,
    options?: RequestInit
): Promise<T> {

    const response = await fetch(
        `${API_BASE}${path}`,
        options
    );

    if (!response.ok) {

        const text =
            await response.text();

        throw new Error(
            `API error ${response.status}: ${text}`
        );
    }

    return response.json() as Promise<T>;
}


export const api = {

    // ========================================================
    // VIDEO
    // ========================================================

    uploadVideo: async (
        file: File
    ): Promise<Video> => {

        const formData = new FormData();

        formData.append(
            "file",
            file
        );

        return request<Video>(
            "/api/videos/upload",
            {
                method: "POST",
                body: formData,
            }
        );
    },


    analyzeVideo: async (
        videoId: number
    ): Promise<AnalysisStatus> => {

        return request<AnalysisStatus>(
            `/api/videos/${videoId}/analyze`,
            {
                method: "POST",
            }
        );
    },


    getVideo: (
        videoId: number
    ): Promise<Video> => {

        return request<Video>(
            `/api/videos/${videoId}`
        );
    },


    getVideoReport: (
        videoId: number
    ): Promise<AnalysisReport> => {

        return request<AnalysisReport>(
            `/api/videos/${videoId}/report`
        );
    },


    getVideoEvents: (
        videoId: number
    ): Promise<EventItem[]> => {

        return request<EventItem[]>(
            `/api/videos/${videoId}/events`
        );
    },


    getAlerts: (): Promise<AlertItem[]> => {

        return request<AlertItem[]>(
            "/api/alerts"
        );
    },


    getEvents: (): Promise<EventItem[]> => {

        return request<EventItem[]>(
            "/api/events"
        );
    },


    deleteVideo: async (
        videoId: number
    ): Promise<void> => {

        const response = await fetch(
            `${API_BASE}/api/videos/${videoId}`,
            {
                method: "DELETE",
            }
        );

        if (!response.ok) {

            const text =
                await response.text();

            throw new Error(
                `Delete failed ${response.status}: ${text}`
            );
        }
    },


    // ========================================================
    // GENERATED VIDEO
    // ========================================================

    getAnnotatedVideoUrl: (
        videoId: number
    ): string => {

        return `${API_BASE}/generated/${videoId}_annotated.mp4`;
    },


    getReportUrl: (
        videoId: number
    ): string => {

        return `${API_BASE}/generated/${videoId}_report.json`;
    },


    getEventsFileUrl: (
        videoId: number
    ): string => {

        return `${API_BASE}/generated/${videoId}_events.json`;
    },


    // ========================================================
    // LIVE CAMERA
    // ========================================================

    liveHealth: async (): Promise<{
        status: string;
        message: string;
    }> => {

        return request(
            "/api/live/health"
        );
    },


    detectLiveFrame: async (
        blob: Blob
    ): Promise<LiveDetectionResponse> => {

        const formData = new FormData();

        formData.append(
            "file",
            blob,
            "webcam.jpg"
        );

        return request<LiveDetectionResponse>(
            "/api/live/detect",
            {
                method: "POST",
                body: formData,
            }
        );
    },
};