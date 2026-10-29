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

      // If overview does not contain model evaluation metrics yet, pull from model-health telemetry or ml/history
      if (overviewRes.data && overviewRes.data.model_wape == null) {
        try {
          const healthRes = await api.get("/api/v1/analytics/model-health");
          let hwape = healthRes.data?.avg_wape ?? healthRes.data?.wape ?? healthRes.data?.latest_run?.wape;
          
          if (hwape == null) {
            const histRes = await api.get("/api/v1/ml/history");
            const firstRun = histRes.data?.runs?.[0];
            hwape = firstRun?.metrics?.wape;
          }

          if (hwape != null) {
            let numWape = Number(hwape);
            if (!isNaN(numWape)) {
              if (numWape <= 1.5) numWape = numWape * 100;
              while (numWape > 100 && numWape <= 10000) numWape = numWape / 100;
              const roundedWape = Math.round(Math.min(100, Math.max(0, numWape)) * 10) / 10;
              overviewRes.data.model_wape = roundedWape;
              overviewRes.data.model_accuracy = Math.round(Math.max(0, 100 - roundedWape) * 10) / 10;
            }
          }
        } catch {
          // Fallback silently if telemetry endpoints unavailable
        }
      }

      return {
        overview: overviewRes.data,
        forecast: forecastRes.data
      };
    },
  });
};
