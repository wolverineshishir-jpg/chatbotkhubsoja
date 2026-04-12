import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="empty-state">
      <p>The requested route does not exist in the current frontend foundation.</p>
      <Link className="text-link" to="/">
        Back to dashboard
      </Link>
    </div>
  );
}
