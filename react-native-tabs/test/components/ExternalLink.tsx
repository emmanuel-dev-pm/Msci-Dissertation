import { Link } from 'expo-router';
import * as WebBrowser from 'expo-web-browser';
import React from 'react';
import { Platform, StyleSheet } from 'react-native';

export function ExternalLink(
  props: Omit<React.ComponentProps<typeof Link>, 'href'> & { href: string }
) {
  const { style, ...rest } = props as any;
  const flattenedStyle = StyleSheet.flatten(style);

  return (
    <Link
      target="_blank"
      // @ts-expect-error: External URLs are not typed.
      href={props.href}
      {...rest}
      style={flattenedStyle}
      onPress={(e) => {
        if (Platform.OS !== 'web') {
          // Prevent the default behavior of linking to the default browser on native.
          e.preventDefault();
          // Open the link in an in-app browser.
          WebBrowser.openBrowserAsync(props.href as string);
        }
      }}
    />
  );
}
