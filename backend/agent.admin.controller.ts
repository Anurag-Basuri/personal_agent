import { Request, Response } from 'express';
import { prisma } from './lib/prisma.js';
import { ApiResponse } from './utils/ApiResponse.js';

export const getAgentSessions = async (req: Request, res: Response) => {
	const page = parseInt(req.query.page as string) || 1;
	const limit = parseInt(req.query.limit as string) || 10;
	const skip = (page - 1) * limit;

	const sessions = await prisma.agentSession.findMany({
		skip,
		take: limit,
		orderBy: { updatedAt: 'desc' },
	});

	const total = await prisma.agentSession.count();

	ApiResponse.ok(
		res,
		{ sessions, total, page, totalPages: Math.ceil(total / limit) },
		'Agent sessions retrieved successfully',
	);
};

export const deleteAgentSession = async (req: Request, res: Response) => {
	const id = req.params.id as string;
	try {
		await prisma.agentSession.delete({
			where: { id },
		});
		ApiResponse.ok(res, null, 'Agent session deleted successfully');
	} catch (error: any) {
		if (error?.code === 'P2025') {
			ApiResponse.ok(res, null, 'Session already deleted');
		} else {
			throw error;
		}
	}
};
