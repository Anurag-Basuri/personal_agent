import { tool } from '@langchain/core/tools';
import { z } from 'zod';
import { prisma } from '../lib/prisma.js';
import sanitizeHtml from 'sanitize-html';

export const submitContactTool = tool(
	async ({ name, email, message }) => {
		try {
			console.log(`[contact.tool] Submitting lead from ${name} <${email}>`);

			// Basic sanitization to prevent XSS from raw text injection
			const cleanName = sanitizeHtml(name, { allowedTags: [] });
			const cleanEmail = sanitizeHtml(email, { allowedTags: [] });
			const cleanMessage = sanitizeHtml(message, { allowedTags: [] });

			await prisma.contactMessage.create({
				data: {
					name: cleanName,
					email: cleanEmail,
					subject: 'Contact Form via AI Agent',
					message: cleanMessage,
					isRead: false,
				},
			});

			return JSON.stringify({
				success: true,
				notification:
					'Successfully saved the message to the database. Anurag will see this in his admin dashboard.',
			});
		} catch (error) {
			console.error('[contact.tool] Error:', error);
			return JSON.stringify({
				success: false,
				error: 'Database error occurred while saving the lead.',
			});
		}
	},
	{
		name: 'submit_contact_lead',
		description:
			'Submit an inquiry, job offer, or contact message to Anurag. You MUST ask the user for their name, email, and message explicitly before calling this tool.',
		schema: z.object({
			name: z.string().describe("Visitor's full name"),
			email: z.string().email().describe("Visitor's valid email address"),
			message: z.string().describe('The inquiry or message'),
		}),
	},
);
