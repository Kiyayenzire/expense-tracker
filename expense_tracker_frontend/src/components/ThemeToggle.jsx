


// src/components/ThemeToggle.jsx
import { IconButton } from "@mui/material";
import { Brightness4, Brightness7 } from "lucide-react"; // or any icons you like

export default function ThemeToggle({ darkMode, setDarkMode }) {
  return (
    <IconButton onClick={() => setDarkMode(!darkMode)} color="inherit">
      {darkMode ? <Brightness7 /> : <Brightness4 />}
    </IconButton>
  );
}


