/// <reference types="@sveltejs/kit" />

declare namespace App {
  interface Locals {
    user: {
      id: number;
      email: string;
      name: string;
      role: string;
      token_balance: number;
    } | null;
    token: string | null;
  }

  interface PageData {
    user: App.Locals['user'];
    locale: string;
  }

  interface Error {
    message: string;
    code?: number;
  }
}
