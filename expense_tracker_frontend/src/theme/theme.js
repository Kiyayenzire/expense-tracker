

// src/theme/theme.js
import { createTheme } from "@mui/material/styles";

export const lightTheme = {
  palette: {
    mode: "light",
    primary: {
      main: "#1E3A8A", // deep corporate blue
    },
    secondary: {
      main: "#F97316", // modern SaaS orange
    },
    background: {
      default: "#F1F5F9", // soft silver
      paper: "#FFFFFF",
    },
    text: {
      primary: "#0F172A",
      secondary: "#1E3A8A",
    },
  },
  shape: {
    borderRadius: 12, // soft rounded corners
  },
};

export const darkTheme = {
  palette: {
    mode: "dark",
    primary: {
      main: "#3B82F6", // lighter blue for brand
    },
    secondary: {
      main: "#FB923C", // CTA orange
    },
    background: {
      default: "#0F172A",
      paper: "#1E293B",
    },
    text: {
      primary: "#F8FAFC",
      secondary: "#60A5FA",
    },
  },
  shape: {
    borderRadius: 12,
  },
};

export const getTheme = (mode) =>
  createTheme(mode === "dark" ? darkTheme : lightTheme);


