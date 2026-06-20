import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ cookies }) => {
  cookies.delete('neuralpulse_token', { path: '/' });
  throw redirect(302, '/');
};
