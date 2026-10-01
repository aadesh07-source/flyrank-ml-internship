/**
 * LoadingSpinner — Loading state indicator (SPECS §13.2).
 */
import { Spinner } from 'react-bootstrap';

export default function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div className="loading-spinner">
      <Spinner animation="border" size="sm" className="me-2" />
      <span>{message}</span>
    </div>
  );
}
