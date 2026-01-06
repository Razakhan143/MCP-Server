# 🚀 Project Tracker MCP Server

A **Model Context Protocol (MCP)** server for managing projects and tasks with PostgreSQL backend. Think of it as a lightweight **Jira/Trello** that Claude can interact with directly!

## 📋 Features

### Core Functionality
- **Users**: Create and manage user accounts
- **Projects**: Organize work into projects with descriptions
- **Tasks**: Track tasks with status (todo, in-progress, done) and deadlines
- **PostgreSQL**: Production-ready relational database with foreign keys and indexes

### MCP Tools (21 Available)

#### User Management (5 tools)
- `create_user` - Create new users
- `get_user` - Get user details
- `list_users` - List all users
- `update_user` - Update user information
- `delete_user` - Delete users

#### Project Management (5 tools)
- `create_project` - Create new projects
- `get_project` - Get project details
- `list_projects` - List all or filter by user
- `update_project` - Update project information
- `delete_project` - Delete projects

#### Task Management (6 tools)
- `create_task` - Create new tasks
- `get_task` - Get task details
- `list_tasks` - List/filter tasks by project and status
- `update_task` - Update task information
- `delete_task` - Delete tasks
- `get_task_statistics` - View task statistics by status

## 🗄️ Database Schema

```sql
users
 ├── id (SERIAL PRIMARY KEY)
 ├── name (VARCHAR)
 ├── email (VARCHAR UNIQUE)
 └── created_at (TIMESTAMP)

projects
 ├── id (SERIAL PRIMARY KEY)
 ├── user_id (FK → users)
 ├── title (VARCHAR)
 ├── description (TEXT)
 └── created_at (TIMESTAMP)

tasks
 ├── id (SERIAL PRIMARY KEY)
 ├── project_id (FK → projects)
 ├── title (VARCHAR)
 ├── status (todo/in-progress/done)
 ├── deadline (DATE)
 └── created_at (TIMESTAMP)
```

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.11+
- PostgreSQL 12+ installed and running
- `uv` (Python package manager) or `pip`

### 1. Install PostgreSQL

**Windows:**
```powershell
# Download from https://www.postgresql.org/download/windows/
# Or using Chocolatey:
choco install postgresql
```

**Mac:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Linux:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2. Create Database

```bash
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE project_tracker;

# Exit psql
\q
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and set your PostgreSQL credentials
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=project_tracker
# DB_USER=postgres
# DB_PASSWORD=your_password
```

### 4. Install Dependencies

```bash
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

### 5. Initialize Database

The database schema will be automatically created when you first run the server:

```bash
uv run main.py
```

## 🎯 Usage with Claude Desktop

### Configure Claude Desktop

Add this to your Claude Desktop config (`claude_desktop_config.json`):

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "project-tracker": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\tesla\\Desktop\\MCP-Server",
        "run",
        "main.py"
      ]
    }
  }
}
```

**Mac/Linux:**
```json
{
  "mcpServers": {
    "project-tracker": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/MCP-Server",
        "run",
        "main.py"
      ]
    }
  }
}
```

### Restart Claude Desktop

After updating the config, restart Claude Desktop to load the MCP server.

## 💬 Example Interactions with Claude

Once configured, you can interact with the server through Claude:

```
You: "Create a new user named John Doe with email john@example.com"

You: "Create a project called 'Website Redesign' for user ID 1"

You: "Add a task 'Design homepage mockup' to project 1 with status todo and deadline 2026-01-15"

You: "Show me all tasks in project 1"

You: "Update task 1 to in-progress status"

You: "Get task statistics for all projects"
```

## 📦 Project Structure

```
MCP-Server/
├── main.py           # MCP server with all tools
├── database.py       # PostgreSQL connection & schema
├── users.py          # User CRUD operations
├── projects.py       # Project CRUD operations
├── tasks.py          # Task CRUD operations
├── pyproject.toml    # Project dependencies
├── .env              # Database configuration (not in git)
├── .env.example      # Example configuration
└── README.md         # This file
```

## 🔧 Development

### Testing the Server Locally

```bash
# Run the server
uv run main.py
```

### Manual Database Queries

```bash
# Connect to database
psql -U postgres -d project_tracker

# Example queries
SELECT * FROM users;
SELECT * FROM projects WHERE user_id = 1;
SELECT * FROM tasks WHERE status = 'in-progress';
```

## 🚨 Troubleshooting

### Database Connection Issues

1. Ensure PostgreSQL is running:
   ```bash
   # Windows
   Get-Service postgresql*
   
   # Mac
   brew services list
   
   # Linux
   sudo systemctl status postgresql
   ```

2. Check `.env` file has correct credentials

3. Test connection:
   ```bash
   psql -U postgres -d project_tracker
   ```

### MCP Server Not Showing in Claude

1. Check `claude_desktop_config.json` path is correct
2. Restart Claude Desktop completely
3. Check logs in Claude Desktop (Help → View Logs)

## 🎓 Learning Resources

- [MCP Documentation](https://modelcontextprotocol.io)
- [FastMCP Guide](https://github.com/jlowin/fastmcp)
- [PostgreSQL Tutorial](https://www.postgresql.org/docs/current/tutorial.html)

## 📝 License

MIT License - feel free to use this for learning and projects!

## 🤝 Contributing

This is a learning project! Feel free to:
- Add new features (tags, comments, attachments)
- Improve error handling
- Add authentication
- Create a web UI

---

**Built with ❤️ using FastMCP and PostgreSQL**

