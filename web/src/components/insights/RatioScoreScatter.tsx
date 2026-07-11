"use client";

import {
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { SCORE_DOMAIN, formatChartDate, type ScatterPoint } from "@/lib/insights";
import { AXIS_TICK, ChartTooltipCard, GRID_PROPS } from "./chart-theme";

interface RatioScoreScatterProps {
  points: ScatterPoint[];
  targetRatio: number;
}

export function RatioScoreScatter({ points, targetRatio }: RatioScoreScatterProps) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <ScatterChart margin={{ top: 16, right: 12, bottom: 0, left: -22 }}>
        <CartesianGrid {...GRID_PROPS} vertical />
        <XAxis
          dataKey="ratio"
          type="number"
          name="Brew ratio"
          domain={["auto", "auto"]}
          tick={AXIS_TICK}
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          tickFormatter={(value: number) => value.toFixed(2)}
        />
        <YAxis
          dataKey="rating"
          type="number"
          name="Score"
          domain={[...SCORE_DOMAIN]}
          tickCount={6}
          tick={AXIS_TICK}
          tickLine={false}
          axisLine={false}
        />
        <ReferenceLine
          x={targetRatio}
          stroke="var(--muted-foreground)"
          strokeDasharray="4 3"
          label={{
            value: `target ${targetRatio.toFixed(1)}`,
            position: "insideTopLeft",
            fill: "var(--muted-foreground)",
            fontSize: 10,
            offset: 8,
          }}
        />
        <Tooltip
          cursor={{ strokeDasharray: "3 3", stroke: "var(--border)" }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null;
            const point = payload[0].payload as ScatterPoint;
            return (
              <ChartTooltipCard
                title={formatChartDate(point.dateMs)}
                rows={[
                  { label: "Brew ratio", value: point.ratio.toFixed(2) },
                  { label: "Score", value: `${point.rating}/10` },
                ]}
              />
            );
          }}
        />
        <Scatter
          data={points}
          fill="var(--chart-1)"
          fillOpacity={0.75}
          isAnimationActive={false}
        />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
