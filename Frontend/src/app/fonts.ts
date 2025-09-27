import localFont from "next/font/local"

export const fkGrotesk = localFont({
  variable: '--font-grotesk',
  display: 'swap',
  src: [
    {
      path: '../../public/fonts/fk-grotesk-neue-font-family/FKGroteskNeueTrial-Thin-BF6576818c2a14c.otf',
      weight: '100',
      style: 'normal',
    },
    {
      path: '../../public/fonts/fk-grotesk-neue-font-family/FKGroteskNeueTrial-Light-BF6576818c0f3e8.otf',
      weight: '300',
      style: 'normal',
    },
    {
      path: '../../public/fonts/fk-grotesk-neue-font-family/FKGroteskNeueTrial-Regular-BF6576818c3af74.otf',
      weight: '400',
      style: 'normal',
    },
    {
      path: '../../public/fonts/fk-grotesk-neue-font-family/FKGroteskNeueTrial-Medium-BF6576818c3a00a.otf',
      weight: '500',
      style: 'normal',
    },
    {
      path: '../../public/fonts/fk-grotesk-neue-font-family/FKGroteskNeueTrial-Bold-BF6576818bd3700.otf',
      weight: '700',
      style: 'normal',
    },
    {
      path: '../../public/fonts/fk-grotesk-neue-font-family/FKGroteskNeueTrial-Black-BF6576818b4c472.otf',
      weight: '900',
      style: 'normal',
    },
  ],
})

