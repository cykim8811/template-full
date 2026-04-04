"use client";

import { useAuth } from "@/hooks/use-auth";
import { UserMenu } from "@/components/user-menu";

export default function Home() {
  const { user } = useAuth();

  return (
    <div className="flex min-h-full flex-1 flex-col">
      <header className="flex items-center justify-between border-b px-6 py-3">
        <h1 className="text-lg font-semibold">Coders</h1>
        <UserMenu />
      </header>
      <main className="flex flex-1 items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-semibold tracking-tight">
            Welcome, {user?.username}
          </h2>
          <p className="mt-2 text-muted-foreground">
            Edit this page to get started.
          </p>
        </div>
      </main>
    </div>
  );
}
