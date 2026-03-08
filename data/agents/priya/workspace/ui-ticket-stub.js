// Base-level ticket management UI stub (#1)
// Assumes React structure

// TODO: Replace dummy data with real backend hookups
// TODO: Add proper styling per Zoe's design
// TODO: Add validation and error states

const TicketList = () => {
  const [tickets, setTickets] = useState([
    { id: '1', title: 'Implement dashboard metrics', status: 'open' },
    { id: '2', title: 'Fix alert thresholds', status: 'in-progress' }
  ]);

  return (
    <div className="ticket-container">
      <h2>Ticket Management</h2>
      <form>
        <input type="text" placeholder="Ticket title" /> 
        <select name="priority">
          <option value="1">High</option>
          <option value="2">Medium</option>
          <option value="3">Low</option>
        </select>
        <button type="submit">Add Ticket</button>
      </form>

      <div className="ticket-list">
        {tickets.map(ticket => (
          <div key={ticket.id} className={`ticket ${ticket.status}`}>
            <h3>{ticket.title}</h3>
            <span>Priority: {ticket.priority}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// # TODO: Add test for TicketList component