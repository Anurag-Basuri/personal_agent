import { Router } from 'express';
import { getAgentSessions, deleteAgentSession } from './agent.admin.controller.js';
import { asyncHandler } from './utils/asyncHandler.js';

const router = Router();

router.get('/agent-sessions', asyncHandler(getAgentSessions));
router.delete('/agent-sessions/:id', asyncHandler(deleteAgentSession));

export default router;
