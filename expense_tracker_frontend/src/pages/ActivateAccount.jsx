
// src/pages/ActivateAccount.jsx


import { useEffect } from "react";
import { useParams } from "react-router-dom";

export default function ActivateAccount() {

  const { token } = useParams();

  useEffect(() => {

    window.location.href = `http://localhost:8000/api/users/activate/${token}/`;

  }, [token]);

  return <div>Activating account...</div>;

}

