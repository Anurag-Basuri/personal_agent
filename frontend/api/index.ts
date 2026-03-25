const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

export const apiClient = {
	async post<T>(path: string, body: unknown): Promise<T> {
		const res = await fetch(`${baseUrl}${path}`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(body),
		});

		const data = await res.json().catch(() => ({}));

		if (!res.ok) {
			throw { response: { data } };
		}

		return (data?.data ?? data) as T;
	},
};
