"use client"

import * as React from "react"

type SmoothScrollLinkProps = React.ComponentProps<"a">

export default function SmoothScrollLink({ href, onClick, ...rest }: SmoothScrollLinkProps) {
  const handleClick: React.MouseEventHandler<HTMLAnchorElement> = (e) => {
    if (href && href.startsWith("#")) {
      const id = href.slice(1)
      const target = document.getElementById(id)
      if (target) {
        e.preventDefault()
        target.scrollIntoView({ behavior: "smooth", block: "start" })
      }
    }
    onClick?.(e)
  }

  return <a href={href} onClick={handleClick} {...rest} />
}

