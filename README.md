💸 Splitwise Clone:-
A full-stack Splitwise Clone built for managing and tracking shared expenses among friends and groups. Users can create groups, add expenses, view balances, and settle debts — all wrapped in a sleek glassmorphism-based futuristic UI.

🚀 Features:-
1.🔐 User System (Accounts & Auth)
  ✅ User registration, login, and logout
  ✅ Extended Profile model with avatar, bio, etc.
  ⚙️ Friendships — add, accept, or remove friends

2.👥 Groups System:-
  ✅ Create / Update / Delete groups
  ✅ Add or remove group members
  ✅ Categorize groups (Trip, Home, Event, etc.)
  ✅ Group detail page 
  ✅ JSON member export for expense forms

3.💰 Expense System:-
  ✅ Expense and ExpenseShare models
  ✅ Add expense (equal / unequal / percentage split)
  ✅ Edit / Delete expense
  ✅ Detailed breakdown view + PDF download

4.⚖️ Balances & Settlements:-
  ✅ Per-user owed/owes calculations
  ✅ Group-level balance matrix
  ✅ Record settlements (payments)
  ✅ Simplify debts algorithm

5.📊 Dashboard & Analytics:-
  ✅ Dashboard overview of user activity
  ✅ Total groups, expenses, and balances
  ✅ Recent activity feed
  ✅ Charts and insights for expense visualization

6.🔔 Notifications & Messages:-
  ✅ In-app notifications
  ✅ Activity alerts (e.g., “X added an expense in Goa Trip”)
  ✅ Real-time updates for expenses and groups

7.🎨 UI / UX & Design System:-
  ✅ Modern glassmorphism gradient design
  ✅ Reusable components (forms, buttons, modals)
  ✅ Fully responsive layout
  ✅ Subtle animations and hover effects

🧩 Tech Stack:-
  >(Update based on your project — example below)
  >Backend: Django / Django REST Framework
  >Frontend: HTML, CSS, JavaScript / TailwindCSS
  >Database: PostgreSQL / SQLite
  >Other: Chart.js for analytics, Django messages & signals for notifications

📂 Setup Instructions:-
  # Clone the repository
  git clone https://github.com/yourusername/splitwise-clone.git
  
  # Navigate to the project folder
  cd splitwise-clone
  
  # Setup virtual environment (Python)
  python -m venv env
  source env/bin/activate  # or env\Scripts\activate on Windows
  
  # Install dependencies
  pip install -r requirements.txt
  
  # Run migrations
  python manage.py migrate
  
  # Start the server
  python manage.py runserver

🧠 Inspiration

Inspired by Splitwise, this clone replicates its expense-sharing logic while integrating advanced analytics and a refined futuristic UI.



