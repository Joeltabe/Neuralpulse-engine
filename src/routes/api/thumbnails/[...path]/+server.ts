import { json, type RequestHandler } from '@sveltejs/kit';
import { readFile } from 'fs/promises';
import { join } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const THUMBNAILS_DIR = join(__dirname, '../../../../frontend/thumbnails');

export const GET: RequestHandler = async ({ params }) => {
  try {
    const filePath = params.path;
    if (!filePath || filePath.includes('..')) {
      return new Response('Not found', { status: 404 });
    }

    const fullPath = join(THUMBNAILS_DIR, filePath);
    
    // Prevent directory traversal
    if (!fullPath.startsWith(THUMBNAILS_DIR)) {
      return new Response('Not found', { status: 404 });
    }

    const buffer = await readFile(fullPath);
    
    // Determine content type
    const ext = filePath.split('.').pop()?.toLowerCase();
    const mimeTypes: Record<string, string> = {
      png: 'image/png',
      jpg: 'image/jpeg',
      jpeg: 'image/jpeg',
      gif: 'image/gif',
      webp: 'image/webp'
    };
    
    const contentType = mimeTypes[ext || ''] || 'application/octet-stream';
    
    return new Response(buffer, {
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=3600'
      }
    });
  } catch (error) {
    return new Response('Not found', { status: 404 });
  }
};
