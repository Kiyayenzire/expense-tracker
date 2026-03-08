


// src/pages/Dashboard.jsx
import { useState, useEffect } from "react";
import { Container, Typography, Button, Stack, Card, CardContent } from "@mui/material";
import dayjs from "dayjs";

import ExpenseForm from "../features/expenses/ExpenseForm";
import ExpenseTable from "./ExpenseTable";
import { getExpensesByDate } from "../features/expenses/expenseService";

export default function Dashboard() {
  const [open, setOpen] = useState(false);
  const [expenses, setExpenses] = useState([]);
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
        Dashboard
      </Typography>

      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ mb: 3 }}>
        <Button
          variant="contained"
          color="primary"
          sx={{ borderRadius: 2, textTransform: "none", px: 3 }}
          onClick={() => setOpen(true)}
        >
          + Add Expense
        </Button>

        <Button
          variant="outlined"
          color="secondary"
          sx={{
            borderRadius: 2,
            textTransform: "none",
            px: 3,
            "&:hover": { borderColor: "secondary.main", backgroundColor: "secondary.light", color: "white" },
          }}
        >
          View Expenses
        </Button>
      </Stack>

      <Card sx={{ borderRadius: 2, boxShadow: 3, mb: 3 }}>
        <CardContent>
          <ExpenseTable expenses={expenses} />
        </CardContent>
      </Card>

      <ExpenseForm open={open} handleClose={() => setOpen(false)} refreshExpenses={fetchExpenses} />
    </Container>
  );
}


