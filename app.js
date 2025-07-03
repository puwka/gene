import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';
import { createClient } from '@supabase/supabase-js';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// Supabase client
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_ANON_KEY);
const supabaseAdmin = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use('/static', express.static(path.join(__dirname, 'static')));

// Routes
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'templates', 'index.html'));
});

app.get('/about', (req, res) => {
  res.sendFile(path.join(__dirname, 'templates', 'about.html'));
});

app.get('/features', (req, res) => {
  res.sendFile(path.join(__dirname, 'templates', 'features.html'));
});

app.get('/contacts', (req, res) => {
  res.sendFile(path.join(__dirname, 'templates', 'contacts.html'));
});

// Check authentication status
app.get('/api/check-auth', async (req, res) => {
  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (user) {
      // Get username from profiles table
      const { data: profile, error } = await supabase
        .from('profiles')
        .select('username')
        .eq('id', user.id)
        .single();
      
      if (error) throw error;
      
      return res.json({
        authenticated: true,
        username: profile?.username || user.email
      });
    }
    res.json({ authenticated: false });
  } catch (err) {
    console.error('Auth check error:', err);
    res.status(500).json({ error: 'Ошибка проверки аутентификации' });
  }
});

app.post('/api/register', async (req, res) => {
    const { login, email, password } = req.body;
  
    // Валидация
    if (!email || !password || !login) {
      return res.status(400).json({ error: 'Все поля обязательны для заполнения' });
    }
  
    try {
      // 1. Регистрация в Supabase Auth
      const { data: signUpData, error: signUpError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: { username: login }
        }
      });
  
      if (signUpError) throw signUpError;
  
      const user = signUpData.user;
      if (!user) {
        return res.json({ 
          message: 'Проверьте почту для подтверждения регистрации'
        });
      }
  
      // 2. Создание профиля (теперь с email)
      const { error: profileError } = await supabaseAdmin
        .from('profiles')
        .insert([{ 
          id: user.id,
          username: login,
          email: email, // Добавляем email
          created_at: new Date().toISOString()
        }]);
  
      if (profileError) throw profileError;
  
      res.json({ 
        success: true,
        message: 'Регистрация успешна!',
        login 
      });
    } catch (error) {
      console.error('Registration error:', error);
      res.status(400).json({ 
        error: error.message || 'Ошибка регистрации' 
      });
    }
  });

// Login
app.post('/api/login', async (req, res) => {
  const { login, password } = req.body;
  
  try {
    // 1. Find user by username in profiles table
    const { data: profile, error: profileError } = await supabase
      .from('profiles')
      .select('id')
      .eq('username', login)
      .single();
    
    if (profileError || !profile) {
      return res.status(400).json({ error: 'Неверный логин или пароль' });
    }
    
    // 2. Get user email from auth.users
    const { data: user, error: userError } = await supabaseAdmin
      .from('users')
      .select('email')
      .eq('id', profile.id)
      .single();
    
    if (userError || !user) {
      return res.status(400).json({ error: 'Пользователь не найден' });
    }
    
    // 3. Sign in with email and password
    const { data: authData, error: authError } = await supabase.auth.signInWithPassword({
      email: user.email,
      password
    });
    
    if (authError) throw authError;
    
    res.json({ 
      success: true,
      message: 'Вход выполнен успешно',
      login 
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(400).json({ 
      error: error.message || 'Ошибка входа' 
    });
  }
});

// Logout
app.post('/api/logout', async (req, res) => {
  try {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
    res.json({ success: true, message: 'Выход выполнен успешно' });
  } catch (error) {
    console.error('Logout error:', error);
    res.status(500).json({ error: 'Ошибка при выходе из системы' });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`Сервер запущен на http://localhost:${PORT}`);
});