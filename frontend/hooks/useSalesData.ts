import { useQuery } from "@tanstack/react-query";
import api from "../lib/api";

export interface OverviewParams {
  period?: string;
  startDate?: string;
  endDate?: string;
  sku?: string;
}

export const useSalesData = (params?: OverviewParams) => {
  const period = params?.period || "all";
  const startDate = params?.startDate || "";
  const endDate = params?.endDate || "";
  const sku = params?.sku || "";

  return useQuery({
    queryKey: ["sales-data", "dashboard", period, startDate, endDate, sku],
    queryFn: async () => {
      const queryParams: Record<string, string> = { period };
      if (startDate) queryParams.start_date = startDate;
      if (endDate) queryParams.end_date = endDate;
      if (sku) queryParams.sku = sku;

      const [overviewRes, forecastRes] = await Promise.all([
        api.get("/api/v1/analytics/overview", { params: queryParams }),
        api.get("/api/v1/analytics/forecast", { params: sku ? { sku } : undefined })
      ]);

      // If overview does not contain model evaluation metrics yet, pull from model-health telemetry
      if (overviewRes.data && overviewRes.data.model_wape == null) {
        try {
          const healthRes = await api.get("/api/v1/analytics/model-health");
          if (healthRes.data) {
            const hwape = healthRes.data.avg_wape ?? healthRes.data.wape ?? healthRes.data.latest_run?.wape;
            if (hwape != null) {
              const numWape = Number(hwape);
              const normalizedWape = numWape <= 1.5 ? numWape * 100 : (numWape > 100 && numWape <= 10000 ? numWape / 100 : numWape);
              overviewRes.data.model_wape = Math.round(normalizedWape * 10) / 10;
              overviewRes.data.model_accuracy = Math.round(Math.max(0, 100 - overviewRes.data.model_wape) * 10) / 10;
            }
          }
        } catch {
          // Fallback silently if model-health unavailable
        }
      }

      return {
        overview: overviewRes.data,
        forecast: forecastRes.data
      };
    },
  });
};
