// backend/plugins/oauthPlugin.js
const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();
const passport = require('passport');
const GoogleStrategy = require('passport-google-oauth20').Strategy;
const GitHubStrategy = require('passport-github2').Strategy;
const jwt = require('jsonwebtoken');

const JWT_SECRET = process.env.JWT_SECRET || 'replace_this_with_a_secure_random_value';

function generateToken(user) {
  const payload = { userId: user.id, username: user.username };
  return jwt.sign(payload, JWT_SECRET, { expiresIn: '7d' });
}

// OAuthで取得したプロフィールからユーザーDB反映する関数
async function findOrCreateOAuthUser(provider, providerAccountId, profile) {
  // 既存OAuthAccount検索
  let oauthAccount = await prisma.oAuthAccount.findUnique({
    where: {
      provider_providerAccountId: {
        provider,
        providerAccountId
      }
    },
    include: { user: true }
  });

  if (oauthAccount && oauthAccount.user) {
    return oauthAccount.user;
  }

  // 新規ユーザー作成
  const email = profile.emails && profile.emails[0] ? profile.emails[0].value : null;
  let username = profile.username || profile.displayName || `user_${provider}_${providerAccountId}`;
  // ユーザー名が重複したら適宜suffix追加するなどの処理も可能だがここでは簡易化
  const existingUser = await prisma.user.findUnique({ where: { username } });
  if (existingUser) {
    username = username + '_' + Date.now();
  }

  const user = await prisma.user.create({
    data: {
      username: username,
      email: email || `noemail_${provider}_${providerAccountId}@example.com`,
      passwordHash: '', // OAuthユーザーはパスワード不要
      oAuthAccounts: {
        create: {
          provider,
          providerAccountId
        }
      }
    }
  });
  return user;
}

// Passport戦略設定
function configurePassport() {
  const googleClientID = process.env.GOOGLE_CLIENT_ID;
  const googleClientSecret = process.env.GOOGLE_CLIENT_SECRET;
  if (googleClientID && googleClientSecret) {
    passport.use(new GoogleStrategy({
      clientID: googleClientID,
      clientSecret: googleClientSecret,
      callbackURL: `http://localhost:${process.env.PORT || 4000}/auth/oauth/google/callback`
    }, async (accessToken, refreshToken, profile, done) => {
      try {
        const user = await findOrCreateOAuthUser('google', profile.id, profile);
        done(null, user);
      } catch (err) {
        done(err);
      }
    }));
  }

  const githubClientID = process.env.GITHUB_CLIENT_ID;
  const githubClientSecret = process.env.GITHUB_CLIENT_SECRET;
  if (githubClientID && githubClientSecret) {
    passport.use(new GitHubStrategy({
      clientID: githubClientID,
      clientSecret: githubClientSecret,
      callbackURL: `http://localhost:${process.env.PORT || 4000}/auth/oauth/github/callback`
    }, async (accessToken, refreshToken, profile, done) => {
      try {
        const user = await findOrCreateOAuthUser('github', profile.id, profile);
        done(null, user);
      } catch (err) {
        done(err);
      }
    }));
  }

  passport.serializeUser((user, done) => {
    done(null, user.id);
  });

  passport.deserializeUser(async (id, done) => {
    const user = await prisma.user.findUnique({ where: { id } });
    done(null, user);
  });
}

function applyPlugin(app) {
  configurePassport();
  app.use(passport.initialize());

  // Google用
  app.get('/auth/oauth/google',
    passport.authenticate('google', { scope: ['profile', 'email'] })
  );

  app.get('/auth/oauth/google/callback',
    passport.authenticate('google', { session: false }),
    (req, res) => {
      const token = generateToken(req.user);
      // フロントエンドへリダイレクト
      res.redirect(`http://localhost:3000/oauth?token=${token}`);
    }
  );

  // GitHub用
  app.get('/auth/oauth/github',
    passport.authenticate('github', { scope: ['user:email'] })
  );

  app.get('/auth/oauth/github/callback',
    passport.authenticate('github', { session: false }),
    (req, res) => {
      const token = generateToken(req.user);
      res.redirect(`http://localhost:3000/oauth?token=${token}`);
    }
  );
}

module.exports = {
  applyPlugin
};
