

// src/pages/Login.jsx

import { useState, useContext, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../services/authService";
import { AuthContext } from "../context/AuthContext";

export default function Login() {

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const navigate = useNavigate();

  const { user, login: loginContext } = useContext(AuthContext);

  useEffect(() => {
    if (user) {
      navigate("/");
    }
  }, [user, navigate]);

  const handleSubmit = async (e) => {

    e.preventDefault();

    try {

      const data = await login(email, password);

      loginContext(data);

      navigate("/");

    } catch (error) {

      alert("Invalid credentials or inactive account.");

    }

  };

  return (
    <div style={{ padding: "40px" }}>
      <h2>Login</h2>

      <form onSubmit={handleSubmit}>

        <input
          type="text"
          placeholder="Email or Username"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <br /><br />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <br /><br />

        <button type="submit">Login</button>

      </form>
    </div>
  );

}

