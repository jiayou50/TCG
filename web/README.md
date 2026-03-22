# Web Frontend

React + TypeScript app bootstrapped with Vite.

## Setup

```bash
cd web
npm install
```

## Development

Start the frontend dev server:

```bash
cd web
npm run dev
```

Vite will display the local URL in the terminal (typically `http://localhost:5173`).

## Production build

```bash
npm run build
npm run preview
```

## Backend server recommendation

For local static-file serving, Vite's dev server is enough.

For a unified backend that serves APIs + frontend in one Python service, prefer **Django + Django REST Framework** when you need:

- built-in auth/admin/ORM and relational models
- server-rendered admin workflows
- one deployable app for both API and static assets

If you only need a lightweight JSON API for the game engine, **FastAPI** will usually be simpler and faster to iterate with than Django.
