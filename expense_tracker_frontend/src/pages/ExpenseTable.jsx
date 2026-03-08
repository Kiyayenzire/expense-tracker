


// src/pages/ExpenseTable.jsx
import { Table, TableHead, TableRow, TableCell, TableBody, Stack, Typography } from "@mui/material";

export default function ExpenseTable({ expenses }) {
  if (!expenses || expenses.length === 0) {
    return <Typography>No expenses found for this date.</Typography>;
  }

  return (
    <Stack spacing={3}>
      <Table>
        <TableHead>
          <TableRow sx={{ bgcolor: "primary.main", "& th": { color: "white", fontWeight: "bold" } }}>
            <TableCell>Category</TableCell>
            <TableCell>Item</TableCell>
            <TableCell align="right">Quantity</TableCell>
            <TableCell align="right">Rate</TableCell>
            <TableCell align="right">Amount</TableCell>
            <TableCell>Currency</TableCell>
            <TableCell>Supplier</TableCell>
            <TableCell>Country</TableCell>
            <TableCell>Date</TableCell>
          </TableRow>
        </TableHead>

        <TableBody>
          {expenses.map((exp) => {
            const rate = Number(exp.rate || 0);
            const amount = Number(exp.amount || 0);
            const rateFormatted = rate.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            });
            const amountFormatted = amount.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            });

            return (
              <TableRow key={exp.id} sx={{ "&:hover": { bgcolor: "grey.100" } }}>
                <TableCell>{exp.category_name}</TableCell>
                <TableCell>{exp.item}</TableCell>
                <TableCell align="right">{Number(exp.quantity).toLocaleString()}</TableCell>
                <TableCell align="right">{rateFormatted}</TableCell>
                <TableCell align="right">
                  <strong>{amountFormatted}</strong>
                </TableCell>
                <TableCell>{exp.currency}</TableCell>
                <TableCell>{exp.supplier || "-"}</TableCell>
                <TableCell>{exp.country || "-"}</TableCell>
                <TableCell>{exp.date}</TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </Stack>
  );
}


