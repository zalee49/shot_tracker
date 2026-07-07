"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { SERIES_COLORS, formatChartDate, type ScorePoint } from "@/lib/insights";
import {
  AXIS_TICK,
  ChartTooltipCard,
  GRID_PROPS,
  timeAxisProps,
} from "./chart-theme";

interface ScoreOverTimeChartProps {
  series: { bean: string; points: ScorePoint[]; color: string }[];
}

export function seriesColor(index: number): string {
  return SERIES_COLORS[index % SERIES_COLORS.length];
}

export function ScoreOverTimeChart({ series }: ScoreOverTimeChartProps) {
  return (
    <div>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart margin={{ top: 8, right: 12, bottom: 0, left: -22 }}>
          <CartesianGrid {...GRID_PROPS} />
          <XAxis {...timeAxisProps()} allowDuplicatedCategory={false} />
          <YAxis
            domain={[0, 10]}
            tickCount={6}
            tick={AXIS_TICK}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const point = payload[0].payload as ScorePoint;
              return (
                <ChartTooltipCard
                  title={formatChartDate(point.dateMs)}
                  rows={[
                    {
                      label: point.bean,
                      value: `${point.rating}/10`,
                      color: payload[0].stroke as string,
                    },
                  ]}
                />
              );
            }}
          />
          {series.map(({ bean, points, color }) => (
            <Line
              key={bean}
              data={points}
              dataKey="rating"
              name={bean}
              stroke={color}
              strokeWidth={2}
              dot={{ r: 3, fill: color, strokeWidth: 0 }}
              activeDot={{ r: 5 }}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1.5">
        {series.map(({ bean, color }) => (
          <span key={bean} className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="size-2.5 rounded-full" style={{ background: color }} />
            {bean}
          </span>
        ))}
      </div>
    </div>
  );
}
