# Quick Start Guide: Expo Google Sign-in with Firebase

## 🚀 Overview

This guide will help you set up Google Sign-in with Firebase using Expo's managed workflow - no Android SDK or prebuild required!

---

## 📦 Step 1: Install Dependencies

```bash
cd D:\projects\techaire-google\Msci-Dissertation\react-native-tabs\test

npm install expo-auth-session expo-crypto
```

---

## 🔐 Step 2: Set Up Google Cloud Console

### 2.1 Create/Select a Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one

### 2.2 Enable Google+ API
1. Go to **APIs & Services** > **Library**
2. Search for "Google+ API"
3. Click on it and press **Enable**

### 2.3 Configure OAuth Consent Screen
1. Go to **APIs & Services** > **OAuth consent screen**
2. Select **External** for user type
3. Fill in the required fields:
   - **App name**: Techaire
   - **User support email**: Your email
   - **Developer contact information**: Your email
4. Click **Save and Continue** through all steps
5. Click **Save and Continue** (you can skip scopes and test users for now)

### 2.4 Create OAuth Client ID
1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Select **Web application**
4. **Name**: "Techaire Expo Client"
5. **Authorized JavaScript origins**: Leave empty
6. **Authorized redirect URIs**: 
   ```
   exp://YOUR_EXPO_USERNAME.test.exp.direct:80/--/
   ```
   Replace `YOUR_EXPO_USERNAME` with your Expo account username.
   > 💡 **Tip**: Your Expo username appears in the Expo DevTools when you run `expo start`
   
7. Click **Create**
8. **IMPORTANT**: Copy the **Client ID** (it looks like: `123456789-abc123xyz.apps.googleusercontent.com`)

---

## 🔧 Step 3: Configure Your App

### 3.1 Update GoogleSignIn Component

Open `components/GoogleSignIn.jsx` and replace `YOUR_GOOGLE_CLIENT_ID_HERE` with your actual Client ID:

```javascript
const [request, response, promptAsync] = AuthSession.useAuthRequest(
  {
    clientId: "123456789-abc123xyz.apps.googleusercontent.com", // Paste your Client ID here
    scopes: ["openid", "profile", "email"],
    redirectUri: AuthSession.makeRedirectUri({
      scheme: undefined,
    }),
  },
  {
    authorizationEndpoint: "https://accounts.google.com/o/oauth2/v2/auth",
    tokenEndpoint: "https://oauth2.googleapis.com/token",
  },
);
```

### 3.2 Verify Firebase Configuration

Make sure you have:
- ✅ `google-services.json` in your project root (Android Firebase config)
- ✅ `GoogleService-Info.plist` in your project root (iOS Firebase config)

These should already be there from your previous setup.

### 3.3 Add Scheme (Optional)

If you want to use a custom scheme for deep linking, add it to `app.json`:

```json
{
  "expo": {
    "scheme": "techaire",
    "name": "test",
    "slug": "test"
  }
}
```

Then update the redirect URI in GoogleSignIn.jsx:
```javascript
redirectUri: AuthSession.makeRedirectUri({
  scheme: "techaire",
}),
```

And add this scheme to your Google Cloud Console redirect URIs:
```
exp://techaire.test.exp.direct:80/--/
```

---

## 🧹 Step 4: Clean Up Old Package

Remove the incompatible native package:

```bash
npm uninstall @react-native-google-signin/google-signin
```

---

## ▶️ Step 5: Run Your App

### 5.1 Start Expo DevTools

```bash
cd D:\projects\techaire-google\Msci-Dissertation\react-native-tabs\test
npx expo start
```

### 5.2 Run on Your Phone

1. **Install Expo Go** on your phone:
   - Android: [Play Store](https://play.google.com/store/apps/details?id=host.exp.exponent)
   - iOS: [App Store](https://apps.apple.com/app/expo-go/id982107779)

2. **Scan the QR code** from the Expo DevTools with your phone's camera
3. **The app will open** in Expo Go on your phone

### 5.3 Alternative: Use Android Emulator

If you have Android Studio installed:

```bash
npm run android
```

Or use the Expo DevTools to open in an Android emulator.

---

## 🧪 Step 6: Test Google Sign-in

1. **Navigate to the login screen** in your app
2. **Tap "Sign in with google"**
3. **Expected behavior**:
   - Expo opens a web browser
   - Google's OAuth page appears
   - Select your Google account
   - Browser closes and returns to your app
   - User is signed in with Firebase
   - Check console logs for success message

---

## 🔍 Step 7: View Your Redirect URI

If you're not sure what redirect URI your app is using, add this temporarily to your GoogleSignIn component:

```javascript
useEffect(() => {
  const redirectUri = AuthSession.makeRedirectUri({
    scheme: undefined,
  });
  console.log("🔗 Redirect URI:", redirectUri);
}, []);
```

The redirect URI will be logged in your Expo DevTools console. Make sure this matches what's in your Google Cloud Console!

---

## 🐛 Troubleshooting

### Issue: "Redirect URI mismatch"
**Solution**:
1. Check the logs in Expo DevTools to see what redirect URI is being used
2. Update the authorized redirect URIs in Google Cloud Console to match exactly
3. Make sure you're using the correct Expo username

### Issue: "OAuth error: redirect_uri_mismatch"
**Solution**:
1. In Google Cloud Console, go to Credentials > Your OAuth Client
2. Check the authorized redirect URIs
3. Make sure they include the exact URI your app is using
4. Try adding multiple variations:
   - `exp://YOUR_USERNAME.test.exp.direct:80/--/`
   - `exp://localhost:19000/--/`
   - `exp://192.168.x.x:19000/--/` (your local IP)

### Issue: App doesn't redirect back after Google sign-in
**Solution**:
1. Make sure `WebBrowser.maybeCompleteAuthSession()` is at the top of your file
2. Check that your redirect URI is correctly configured
3. Try adding a custom scheme to `app.json`

### Issue: Firebase authentication fails
**Solution**:
1. Verify `google-services.json` is in the correct location (project root)
2. Make sure Google Sign-in provider is enabled in Firebase Console
3. Check that Firebase is properly initialized

### Issue: "Error: Cannot find module 'expo-auth-session'"
**Solution**:
```bash
# Clear cache and reinstall
rm -rf node_modules
npm install
npx expo start --clear
```

---

## 📱 Creating APK for Distribution

### Option 1: EAS Build (Recommended)

```bash
# Install EAS CLI
npm install -g eas-cli

# Configure EAS
eas build:configure

# Build APK
eas build --platform android --profile preview
```

You'll get a download link for the APK that you can distribute anywhere!

### Option 2: Expo Build Service (Legacy - Deprecated)

```bash
# This is deprecated, but still works
eas build --platform android --profile preview
```

---

## 🌐 Distributing Your APK Outside Play Store

Once you have your APK:

1. **Upload to Google Drive/Dropbox** and share the link
2. **Upload to GitHub** as a release asset
3. **Host on your own server/website**
4. **Email the APK** directly to users

Users will need to:
- Enable "Install from unknown sources" in phone settings
- Download the APK
- Tap to install

---

## ✅ Checklist

Before testing, make sure you have:

- [ ] Installed `expo-auth-session` and `expo-crypto`
- [ ] Created OAuth client in Google Cloud Console
- [ ] Added correct redirect URI to Google Cloud Console
- [ ] Copied Client ID to GoogleSignIn.jsx
- [ ] Removed `@react-native-google-signin/google-signin`
- [ ] Firebase config files are in project root
- [ ] Expo Go installed on your phone
- [ ] Can see your app in Expo Go

---

## 🎯 What's Different from Prebuild?

| Feature | Prebuild | Expo Managed |
|---------|----------|--------------|
| **Setup Time** | 30-60 min | 15-30 min |
| **Android SDK** | Required | Not needed |
| **SHA-1 Fingerprints** | Required | Not needed |
| **Native Code** | Generated | Not needed |
| **Expo Go** | Won't work | ✅ Works |
| **Local Builds** | ✅ Possible | ⚠️ EAS only |
| **Cost** | Free | Free tier 30 builds/mo |
| **Complexity** | High | Low |

---

## 🚀 You're Ready!

You now have Google Sign-in working with Firebase using Expo's managed workflow. This approach is:

- ✅ **Simpler** - No Android SDK or native code
- ✅ **Faster** - Up and running in 15-30 minutes
- ✅ **Easier** - Uses Expo Go for testing
- ✅ **Production-ready** - Can build APKs with EAS
- ✅ **Flexible** - Easy to distribute APKs anywhere

**Happy coding!** 🎉