

// src/components/ExpenseChart.jsx
import { Card, CardContent, Typography, useTheme } from "@mui/material";
import { ResponsiveContainer, PieChart, Pie, Tooltip, Cell } from "recharts";

export default function ExpenseChart({ data }) {
  const theme = useTheme();

  // Use theme colors: primary, secondary, success, danger
  const COLORS = [
    theme.palette.primary.main,
    theme.palette.secondary.main,
    theme.palette.success.main,
    theme.palette.danger.main,
    theme.palette.text.primary,
  ];

  return (
    <Card sx={{ borderRadius: 3, boxShadow: 3 }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 2, color: "text.primary" }}>
          Expenses by Category
        </Typography>

        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              outerRadius={110}
              label
            >
              {data.map((entry, index) => (
                <Cell key={index} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: theme.palette.background.paper,
                borderRadius: 8,
                border: `1px solid ${theme.palette.divider}`,
              }}
              itemStyle={{ color: theme.palette.text.primary }}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

