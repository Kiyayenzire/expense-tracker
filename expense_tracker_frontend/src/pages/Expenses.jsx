


// src/pages/Expenses.jsx
import { useState, useEffect } from "react";
import { Container, Typography, Button, Stack, TextField, Card, CardContent } from "@mui/material";
import dayjs from "dayjs";

import ExpenseTable from "./ExpenseTable";
import ExpenseForm from "../features/expenses/ExpenseForm";
import { getExpensesByDate } from "../features/expenses/expenseService";

export default function Expenses() {
  const [expenses, setExpenses] = useState([]);
  const [open, setOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState(dayjs().format("YYYY-MM-DD"));

  const fetchExpenses = () => {
    getExpensesByDate(selectedDate)
      .then((data) => setExpenses(data))
      .catch(console.error);
  };

  useEffect(() => fetchExpenses(), [selectedDate]);

  return (
    <Container>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Expenses
      </Typography>

      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} alignItems="center" sx={{ mb: 3 }}>
        <TextField
          type="date"
          label="Filter by Date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          InputLabelProps={{ shrink: true }}
        />
        <Button
          variant="contained"
          color="primary"
          sx={{ borderRadius: 2, px: 3, textTransform: "none" }}
          onClick={() => setOpen(true)}
        >
          + Add Expense
        </Button>
      </Stack>

      <Card sx={{ borderRadius: 2, boxShadow: 3 }}>
        <CardContent>
          <ExpenseTable expenses={expenses} />
        </CardContent>
      </Card>

      <ExpenseForm
        open={open}
        handleClose={() => setOpen(false)}
        selectedDate={selectedDate}
        refreshExpenses={fetchExpenses}
      />
    </Container>
  );
}




