// backend/auth/auth.js
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

const JWT_SECRET = process.env.JWT_SECRET || 'replace_this_with_a_secure_random_value';

// 将来的に外部認証プロバイダを登録するためのフック
// 例：applyAuthProvider({ name: 'activitypub', verifyFn: async(...)=>{} })
const externalAuthProviders = [];

function applyAuthProvider(provider) {
  externalAuthProviders.push(provider);
}

// JWTトークン発行
function generateToken(user) {
  const payload = { userId: user.id, username: user.username };
  return jwt.sign(payload, JWT_SECRET, { expiresIn: '7d' }); // 1週間有効例
}

// JWTトークン検証用ミドルウェア
function authMiddleware(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader) return res.status(401).json({ error: 'No token provided' });

  const token = authHeader.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token provided' });

  jwt.verify(token, JWT_SECRET, (err, decoded) => {
    if (err) return res.status(401).json({ error: 'Invalid token' });

    req.user = decoded; // { userId, username }
    next();
  });
}

// ローカルサインアップ処理
async function signupUser({ email, username, password }) {
  // 重複チェック
  const existingEmail = await prisma.user.findUnique({ where: { email } });
  if (existingEmail) throw new Error('Email already in use');
  
  const existingUsername = await prisma.user.findUnique({ where: { username } });
  if (existingUsername) throw new Error('Username already in use');

  const hash = await bcrypt.hash(password, 10);
  const user = await prisma.user.create({
    data: {
      email,
      username,
      passwordHash: hash
    }
  });

  return user;
}

// ローカルログイン処理
async function loginUser({ email, password }) {
  const user = await prisma.user.findUnique({ where: { email } });
  if (!user) throw new Error('Invalid credentials');

  const match = await bcrypt.compare(password, user.passwordHash);
  if (!match) throw new Error('Invalid credentials');

  return user;
}

module.exports = {
  applyAuthProvider,
  generateToken,
  authMiddleware,
  signupUser,
  loginUser
};
