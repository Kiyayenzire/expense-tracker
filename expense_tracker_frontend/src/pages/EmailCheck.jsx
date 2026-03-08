

// src/pages/EmailCheck.jsx

import { useState, useContext, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { checkEmail } from "../services/authService";
import { AuthContext } from "../context/AuthContext";

export default function EmailCheck() {

  const [email, setEmail] = useState("");

  const navigate = useNavigate();

  const { user } = useContext(AuthContext);

  useEffect(() => {
    if (user) {
      navigate("/");
    }
  }, [user, navigate]);

  const handleSubmit = async (e) => {

    e.preventDefault();

    const trimmedEmail = email.trim();

    if (!trimmedEmail) {
      alert("Please enter your email.");
      return;
    }

    // Basic email format validation to avoid server 400s.
    const emailPattern = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
    if (!emailPattern.test(trimmedEmail)) {
      alert("Please enter a valid email address.");
      return;
    }

    try {

      await checkEmail(trimmedEmail);

      navigate("/register", { state: { email: trimmedEmail } });

    } catch (error) {
      const existingEmailMessage =
        error?.response?.data?.email || error?.response?.data?.detail;

      if (typeof existingEmailMessage === "string" && existingEmailMessage.toLowerCase().includes("already")) {
        navigate("/login");
        return;
      }

      const message =
        existingEmailMessage ||
        error?.message ||
        "Unable to connect to the server. Please try again.";

      alert(message);
    }

  };

  return (
    <div style={{ padding: "40px" }}>

      <h2>Start Registration</h2>

      <form onSubmit={handleSubmit}>

        <input
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <br /><br />

        <button type="submit">Continue</button>

      </form>

    </div>
  );

}


