import { Text,View}from 'react-native';
import React from 'react';
import { Link}from 'expo-router';
import { useSafeAreaFrame } from 'react-native-safe-area-context';

const LoginLayout = ({ children }) => {
    const {button}= useSafeAreaInsets()
    return (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', paddingBottom: button }}> 
        <Link href="/login"></Link>
        </View>
    )

}