

// src/components/Navbar.jsx
import { useState, useContext } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Button,
  Menu,
  MenuItem,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import { useNavigate, useLocation } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";

const navItems = [
  { label: "Dashboard", path: "/" },
  { label: "Expenses", path: "/expenses" },
  { label: "Reports", path: "/reports" },
];

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  const { user, logout } = useContext(AuthContext);
  const [anchorEl, setAnchorEl] = useState(null);

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleNav = (path) => {
    navigate(path);
    handleMenuClose();
  };

  return (
    <AppBar position="static" sx={{ bgcolor: "primary.main", mb: 3 }}>
      <Toolbar>
        {isMobile ? (
          <>
            <IconButton
              edge="start"
              color="inherit"
              aria-label="menu"
              sx={{ mr: 2 }}
              onClick={handleMenuOpen}
            >
              <MenuIcon />
            </IconButton>
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
            >
              {navItems.map((item) => (
                <MenuItem
                  key={item.path}
                  selected={location.pathname === item.path}
                  onClick={() => handleNav(item.path)}
                >
                  {item.label}
                </MenuItem>
              ))}
              <MenuItem onClick={() => { logout(); navigate("/login"); }}>
                Logout
              </MenuItem>
            </Menu>
          </>
        ) : (
          <>
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              Expense Tracker
            </Typography>
            {navItems.map((item) => (
              <Button
                key={item.path}
                color={location.pathname === item.path ? "secondary" : "inherit"}
                onClick={() => navigate(item.path)}
                sx={{ textTransform: "none" }}
              >
                {item.label}
              </Button>
            ))}
            {user && (
              <Button
                color="inherit"
                onClick={() => {
                  logout();
                  navigate("/login");
                }}
                sx={{ textTransform: "none" }}
              >
                Logout
              </Button>
            )}
          </>
        )}
      </Toolbar>
    </AppBar>
  );
}


