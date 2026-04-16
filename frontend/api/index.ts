/**
 * API client utility with Google OAuth Bearer token support.
 * 
 * Usage: Pass the apiToken from the NextAuth session to authenticate requests.
 */

const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

export const apiClient = {
	async post<T>(path: string, body: unknown, apiToken?: string): Promise<T> {
		const headers: HeadersInit = {
			'Content-Type': 'application/json',
		};

		if (apiToken) {
			headers['Authorization'] = `Bearer ${apiToken}`;
		}

		const res = await fetch(`${baseUrl}${path}`, {
			method: 'POST',
			headers,
			body: JSON.stringify(body),
		});

		const data = await res.json().catch(() => ({}));

		if (!res.ok) {
			throw { response: { data } };
		}

		return (data?.data ?? data) as T;
	},

	async get<T>(path: string, apiToken?: string): Promise<T> {
		const headers: HeadersInit = {};

		if (apiToken) {
			headers['Authorization'] = `Bearer ${apiToken}`;
		}

		const res = await fetch(`${baseUrl}${path}`, {
			method: 'GET',
			headers,
		});

		const data = await res.json().catch(() => ({}));

		if (!res.ok) {
			throw { response: { data } };
		}

		return (data?.data ?? data) as T;
	},
};
