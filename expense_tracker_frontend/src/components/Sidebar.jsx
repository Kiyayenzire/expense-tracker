

// src/components/Sidebar.jsx
import { useState } from "react";
import {
  Box,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
  Tooltip,
} from "@mui/material";
import {
  Dashboard as DashboardIcon,
  ReceiptLong as ExpensesIcon,
  BarChart as ReportsIcon,
  Menu as MenuIcon,
  ChevronLeft as ChevronLeftIcon,
} from "@mui/icons-material";
import { useNavigate } from "react-router-dom";

export default function Sidebar() {
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  const menuItems = [
    { text: "Dashboard", path: "/", icon: <DashboardIcon /> },
    { text: "Expenses", path: "/expenses", icon: <ExpensesIcon /> },
    { text: "Reports", path: "/reports", icon: <ReportsIcon /> },
  ];

  return (
    <Box
      sx={{
        width: collapsed ? 64 : 200,
        bgcolor: "background.paper",
        borderRight: 1,
        borderColor: "divider",
        display: { xs: "none", md: "block" },
        transition: "width 200ms ease",
      }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: collapsed ? "center" : "space-between",
          p: 1,
        }}
      >
        {!collapsed && <Box component="span" sx={{ fontWeight: "bold" }}>Menu</Box>}
        <IconButton
          size="small"
          onClick={() => setCollapsed((prev) => !prev)}
          sx={{ ml: collapsed ? 0 : 1 }}
        >
          {collapsed ? <MenuIcon /> : <ChevronLeftIcon />}
        </IconButton>
      </Box>

      <List>
        {menuItems.map((item) => (
          <ListItemButton
            key={item.text}
            onClick={() => navigate(item.path)}
            sx={{
              borderRadius: 1,
              justifyContent: collapsed ? "center" : "flex-start",
              "&:hover": { bgcolor: "primary.light", color: "white" },
              mb: 0.5,
            }}
          >
            <ListItemIcon sx={{ minWidth: 0, mr: collapsed ? 0 : 2 }}>
              <Tooltip title={collapsed ? item.text : ""} placement="right">
                {item.icon}
              </Tooltip>
            </ListItemIcon>
            {!collapsed && <ListItemText primary={item.text} />}
          </ListItemButton>
        ))}
      </List>
    </Box>
  );
}


