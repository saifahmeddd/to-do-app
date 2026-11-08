const databaseNames = {
  firestore: 'Firestore',
  mongodb: 'MongoDB',
  postgres: 'PostgreSQL',
  loading: 'Checking…',
  unavailable: 'Unavailable',
};

export default function DatabaseIndicator({ database }) {
  return (
    <span className="database-indicator" role="status">
      Active database: {databaseNames[database] || database}
    </span>
  );
}
