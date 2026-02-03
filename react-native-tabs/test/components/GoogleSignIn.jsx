import { GoogleSignin, statusCodes } from "@react-native-google-signin/google-signin"

import auth from "@react-native-firebase/auth"


const GoogleSignIn = () => {
    const [isSignUp, setIsSignUp] = useState(false)
    
    
   async function onGoogleButtonPress() {
        await GoogleSignin.signOut()
        await GoogleSignin.hasPlayServices({showPlayServicesUpdateDialog:true})

       const googleSignInResult = await GoogleSignin.signIn()
       const googleCredential = auth.GoogleAuthProvider.credential(googleSignInResult.data?.idToken)
       return await auth().signInWithCredential(googleCredential)
}

    return (
        <View>
            <Button
                 color="#4285F4"
                title={isSignUp ? "Already have an account ? Sign in" : "Don't have an account? Sign Up"}
            onPress={()=>setIsSignUp(!setIsSignUp)}
            />

            <Button  color="#4285F4" title="Sign in with google" onPress={()=> onGoogleButtonPress.then(()=> console.log("Sign in google"))
            } />
       </View> 
    )
}

export default GoogleSignIn
