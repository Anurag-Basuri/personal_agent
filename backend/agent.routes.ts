import { Router } from 'express';
import rateLimit from 'express-rate-limit';
import * as AgentController from './agent.controller';

const router = Router();

// Rate limiter for chat endpoint (Stricter than generic APIs)
const chatLimiter = rateLimit({
	windowMs: 60 * 1000, // 1 minute
	max: 15, // Max 15 messages per IP per minute
	message: 'Too many messages sent. Please wait a minute.',
});

router.post('/', chatLimiter, AgentController.sendMessage);
router.post('/reset', AgentController.resetSession); // Clear session memory

export default router;
