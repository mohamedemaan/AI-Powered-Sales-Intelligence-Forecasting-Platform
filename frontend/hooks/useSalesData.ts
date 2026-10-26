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
      return {
        overview: overviewRes.data,
        forecast: forecastRes.data
      };
    },
  });
};
