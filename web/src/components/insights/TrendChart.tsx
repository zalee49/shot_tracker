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
import { formatChartDate, type TrendPoint } from "@/lib/insights";
import { AXIS_TICK, ChartTooltipCard, GRID_PROPS, timeAxisProps } from "./chart-theme";

interface TrendChartProps {
  title: string;
  points: TrendPoint[];
  color: string;
  format: (value: number) => string;
  showRolling?: boolean;
  domain?: [number, number];
}

export function TrendChart({
  title,
  points,
  color,
  format,
  showRolling = false,
  domain,
}: TrendChartProps) {
  if (points.length === 0) return null;
  const hasRolling = showRolling && points.some((point) => point.rolling !== undefined);

  return (
    <div>
      <div className="flex items-baseline justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {title}
        </h3>
        {hasRolling && (
          <span className="text-[0.68rem] text-muted-foreground">
            dashed = 3-shot rolling avg
          </span>
        )}
      </div>
      <ResponsiveContainer width="100%" height={150}>
        <LineChart data={points} margin={{ top: 10, right: 12, bottom: 0, left: -4 }}>
          <CartesianGrid {...GRID_PROPS} />
          <XAxis {...timeAxisProps()} />
          <YAxis
            domain={domain ?? ["auto", "auto"]}
            tick={AXIS_TICK}
            tickLine={false}
            axisLine={false}
            width={42}
            tickFormatter={(value: number) => format(value)}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const point = payload[0].payload as TrendPoint;
              const rows = [{ label: title, value: format(point.value), color }];
              if (hasRolling && point.rolling !== undefined) {
                rows.push({
                  label: "3-shot avg",
                  value: format(point.rolling),
                  color,
                });
              }
              return (
                <ChartTooltipCard title={formatChartDate(point.dateMs)} rows={rows} />
              );
            }}
          />
          {hasRolling && (
            <Line
              dataKey="rolling"
              stroke={color}
              strokeWidth={1.5}
              strokeDasharray="4 3"
              strokeOpacity={0.5}
              dot={false}
              isAnimationActive={false}
            />
          )}
          <Line
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            dot={{ r: 3, fill: color, strokeWidth: 0 }}
            activeDot={{ r: 5 }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
