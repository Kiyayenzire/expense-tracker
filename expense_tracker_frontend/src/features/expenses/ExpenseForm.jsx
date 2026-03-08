


// src/features/expenses/ExpenseForm.jsx

import { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Stack,
  MenuItem,
} from "@mui/material";
import { createExpense } from "./expenseService";

export default function ExpenseForm({ open, handleClose, selectedDate, refreshExpenses }) {
  const [form, setForm] = useState({
    category: "",
    subcategory: "",
    item: "",
    quantity: 1,
    rate: 0,
    currency: "EUR",
    supplier: "",
    country: "",
    date: selectedDate,
  });

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async () => {
    try {
      await createExpense(form);
      refreshExpenses();
      handleClose();

      setForm({
        category: "",
        subcategory: "",
        item: "",
        quantity: 1,
        rate: 0,
        currency: "EUR",
        supplier: "",
        country: "",
        date: selectedDate,
      });
    } catch (error) {
      console.error("Error creating expense:", error);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      fullWidth
      maxWidth="sm"
      PaperProps={{ sx: { borderRadius: 3 } }}
    >
      <DialogTitle>Add Expense</DialogTitle>

      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <TextField
            label="Category"
            name="category"
            value={form.category}
            onChange={handleChange}
            fullWidth
          />

          <TextField
            label="Subcategory"
            name="subcategory"
            value={form.subcategory}
            onChange={handleChange}
            fullWidth
          />

          <TextField
            label="Item"
            name="item"
            value={form.item}
            onChange={handleChange}
            fullWidth
          />

          <TextField
            label="Quantity"
            name="quantity"
            type="number"
            value={form.quantity}
            onChange={handleChange}
            fullWidth
          />

          <TextField
            label="Rate"
            name="rate"
            type="number"
            value={form.rate}
            onChange={handleChange}
            fullWidth
          />

          <TextField
            select
            label="Currency"
            name="currency"
            value={form.currency}
            onChange={handleChange}
            fullWidth
          >
            <MenuItem value="EUR">€</MenuItem>
            <MenuItem value="USD">$</MenuItem>
            <MenuItem value="UGX">UGX</MenuItem>
          </TextField>

          <TextField
            label="Supplier"
            name="supplier"
            value={form.supplier}
            onChange={handleChange}
            fullWidth
          />

          <TextField
            label="Country"
            name="country"
            value={form.country}
            onChange={handleChange}
            fullWidth
          />

          <TextField
            type="date"
            label="Date"
            name="date"
            value={form.date}
            onChange={handleChange}
            InputLabelProps={{ shrink: true }}
            fullWidth
          />
        </Stack>
      </DialogContent>

      <DialogActions sx={{ p: 2 }}>
        <Button
          onClick={handleClose}
          variant="outlined"
          sx={{ borderRadius: 2, textTransform: "none" }}
        >
          Cancel
        </Button>

        <Button
          onClick={handleSubmit}
          variant="contained"
          color="primary"
          sx={{ borderRadius: 2, textTransform: "none", px: 3 }}
        >
          Save Expense
        </Button>
      </DialogActions>
    </Dialog>
  );
}



