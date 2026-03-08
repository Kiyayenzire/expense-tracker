

// src/pages/Register.jsx

import { useState, useContext, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { register } from "../services/authService";
import { AuthContext } from "../context/AuthContext";

export default function Register() {

  const location = useLocation();
  const navigate = useNavigate();

  const { user } = useContext(AuthContext);

  const email = location.state?.email || "";

  useEffect(() => {
    if (user) {
      navigate("/");
    }
  }, [user, navigate]);

  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    password: "",
    confirm_password: "",
  });

  const handleChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {

    e.preventDefault();

    try {

      await register({
        email,
        ...form,
      });

      alert("Account created. Please check your email to activate.");

      navigate("/login");

    } catch {

      alert("Registration failed.");

    }

  };

  return (
    <div style={{ padding: "40px" }}>

      <h2>Register</h2>

      <form onSubmit={handleSubmit}>

        <p>Email: {email}</p>

        <input
          name="first_name"
          placeholder="First Name"
          onChange={handleChange}
          required
        />

        <br /><br />

        <input
          name="last_name"
          placeholder="Last Name"
          onChange={handleChange}
          required
        />

        <br /><br />

        <input
          type="password"
          name="password"
          placeholder="Password"
          onChange={handleChange}
          required
        />

        <br /><br />

        <input
          type="password"
          name="confirm_password"
          placeholder="Confirm Password"
          onChange={handleChange}
          required
        />

        <br /><br />

        <button type="submit">Create Account</button>

      </form>

    </div>
  );

}

